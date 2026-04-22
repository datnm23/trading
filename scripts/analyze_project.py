"""Build a static import/call graph for the trading project (GitNexus-style analysis)."""
import ast
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path("/home/datnm/projects/trading")

class ProjectAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.modules = {}  # path -> {imports, classes, functions, has_main}
        self.dependencies = defaultdict(set)  # module -> set(imported_modules)
        self.reverse_deps = defaultdict(set)  # module -> set(importers)
        self.class_to_module = {}
        self.function_to_module = {}

    def analyze(self):
        for py_file in ROOT.rglob("*.py"):
            if ".git" in str(py_file) or "__pycache__" in str(py_file):
                continue
            self._analyze_file(py_file)
        self._compute_reverse_deps()

    def _module_name(self, path: Path) -> str:
        rel = path.relative_to(ROOT)
        parts = list(rel.with_suffix("").parts)
        # treat __init__ as package name
        if parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)

    def _analyze_file(self, path: Path):
        mod = self._module_name(path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            return
        info = {
            "path": str(path.relative_to(ROOT)),
            "imports": set(),
            "classes": [],
            "functions": [],
            "has_main": False,
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    info["imports"].add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    # relative import: resolve relative to current module
                    base = mod.split(".")
                    if node.module:
                        imp = ".".join(base[:len(base)-node.level]) + "." + node.module
                    else:
                        imp = ".".join(base[:len(base)-node.level])
                    imp = imp.strip(".")
                else:
                    imp = node.module.split(".")[0] if node.module else ""
                if imp:
                    info["imports"].add(imp)
            elif isinstance(node, ast.ClassDef):
                info["classes"].append(node.name)
                self.class_to_module[node.name] = mod
            elif isinstance(node, ast.FunctionDef):
                info["functions"].append(node.name)
                self.function_to_module[node.name] = mod
            elif isinstance(node, ast.If):
                # detect if __name__ == "__main__"
                try:
                    if (isinstance(node.test, ast.Compare) and
                        isinstance(node.test.left, ast.Name) and
                        node.test.left.id == "__name__" and
                        len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Eq) and
                        isinstance(node.test.comparators[0], ast.Constant) and
                        node.test.comparators[0].value == "__main__"):
                        info["has_main"] = True
                except Exception:
                    pass
        self.modules[mod] = info

    def _compute_reverse_deps(self):
        internal = set(self.modules.keys())
        for mod, info in self.modules.items():
            for imp in info["imports"]:
                if imp in internal:
                    self.dependencies[mod].add(imp)
                    self.reverse_deps[imp].add(mod)

    def summary(self):
        entry_points = []
        for mod, info in self.modules.items():
            if info["has_main"]:
                entry_points.append({"module": mod, "path": info["path"], "kind": "__main__"})
        # Also check shell scripts
        for sh in ROOT.glob("scripts/*.sh"):
            entry_points.append({"module": None, "path": str(sh.relative_to(ROOT)), "kind": "shell"})
        for py in ROOT.glob("scripts/*.py"):
            entry_points.append({"module": None, "path": str(py.relative_to(ROOT)), "kind": "script"})

        return {
            "total_modules": len(self.modules),
            "total_classes": len(self.class_to_module),
            "total_functions": len(self.function_to_module),
            "entry_points": entry_points,
            "top_dependencies": {k: list(v) for k, v in sorted(self.dependencies.items(), key=lambda x: -len(x[1]))[:15]},
            "most_imported": {k: list(v) for k, v in sorted(self.reverse_deps.items(), key=lambda x: -len(x[1]))[:15]},
            "layers": self._layer_analysis(),
        }

    def _layer_analysis(self):
        """Group modules by top-level directory as architectural layers."""
        layers = defaultdict(lambda: {"modules": [], "outgoing": set(), "incoming": set()})
        for mod, info in self.modules.items():
            top = mod.split(".")[0] if mod else "root"
            layers[top]["modules"].append(mod)
        for mod, deps in self.dependencies.items():
            top = mod.split(".")[0] if mod else "root"
            for d in deps:
                layers[top]["outgoing"].add(d.split(".")[0])
        for mod, revs in self.reverse_deps.items():
            top = mod.split(".")[0] if mod else "root"
            for r in revs:
                layers[top]["incoming"].add(r.split(".")[0])
        return {k: {"modules": len(v["modules"]), "outgoing": list(v["outgoing"]), "incoming": list(v["incoming"])} for k, v in layers.items()}

if __name__ == "__main__":
    a = ProjectAnalyzer()
    a.analyze()
    result = a.summary()
    print(json.dumps(result, indent=2, default=str))
