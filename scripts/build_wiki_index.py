#!/usr/bin/env python3
"""Build wiki index from Markdown concepts for static frontend display.

Parses all concept files in crawl-wiki/concepts/ into a JSON file
that the frontend can import directly.

Usage:
    python scripts/build_wiki_index.py
    # Outputs: frontend/public/wiki-index.json
"""

import json
import re
from pathlib import Path


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    fm_text = parts[1].strip()
    metadata = {}

    for line in fm_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            # Handle arrays
            if val.startswith("[") and val.endswith("]"):
                val = [
                    v.strip().strip('"').strip("'")
                    for v in val[1:-1].split(",")
                    if v.strip()
                ]
            # Handle quoted strings
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            elif val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            metadata[key] = val

    return metadata


def parse_concept_file(filepath: Path) -> dict:
    """Parse a single concept markdown file."""
    content = filepath.read_text(encoding="utf-8")
    metadata = parse_frontmatter(content)

    # Extract body (after second ---)
    parts = content.split("---", 2)
    body = parts[2].strip() if len(parts) >= 3 else ""

    # Get first paragraph as summary
    summary = ""
    for line in body.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("["):
            summary = line[:200] + ("..." if len(line) > 200 else "")
            break

    return {
        "id": filepath.stem,
        "title": metadata.get("title", filepath.stem),
        "source_url": metadata.get("source_url", ""),
        "tags": metadata.get("tags", []),
        "backlinks": metadata.get("backlinks", []),
        "related_count": (
            int(metadata.get("related_count", 0))
            if metadata.get("related_count")
            else 0
        ),
        "summary": summary,
        "body_preview": body[:500] + ("..." if len(body) > 500 else ""),
    }


def build_index():
    """Build wiki index from all concept files."""
    concepts_dir = Path("crawl-wiki/concepts")
    output_path = Path("frontend/public/wiki-index.json")

    if not concepts_dir.exists():
        print(f"Error: {concepts_dir} not found")
        return

    concepts = []
    for filepath in sorted(concepts_dir.glob("*.md")):
        try:
            concept = parse_concept_file(filepath)
            concepts.append(concept)
        except Exception as e:
            print(f"Warning: Failed to parse {filepath}: {e}")

    # Build hub mapping
    hubs_dir = Path("crawl-wiki/hubs")
    hubs = []
    if hubs_dir.exists():
        for hub_file in sorted(hubs_dir.glob("*.md")):
            try:
                content = hub_file.read_text(encoding="utf-8")
                meta = parse_frontmatter(content)
                # Extract concept list from body
                body = (
                    content.split("---", 2)[2] if len(content.split("---")) >= 3 else ""
                )
                linked_concepts = re.findall(
                    r"\[([^\]]+)\]\(\.\./concepts/([^\)]+)\)", body
                )
                hubs.append(
                    {
                        "id": hub_file.stem,
                        "title": meta.get("title", hub_file.stem),
                        "concepts": [c[1] for c in linked_concepts],
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to parse hub {hub_file}: {e}")

    index = {
        "meta": {
            "total_concepts": len(concepts),
            "total_hubs": len(hubs),
            "version": "1.0",
        },
        "concepts": concepts,
        "hubs": hubs,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Built wiki index: {len(concepts)} concepts, {len(hubs)} hubs")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    build_index()
