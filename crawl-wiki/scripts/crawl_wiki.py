#!/usr/bin/env python3
"""Crawl turtletrading.wiki into structured markdown knowledge graph."""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import markdownify
import requests
import yaml
from bs4 import BeautifulSoup, Comment

BASE_URL = "https://wiki.turtletrading.vn"
OUTPUT_DIR = Path("/home/datnm/projects/trading/crawl-wiki")
MAX_WORKERS = 10
DELAY = 0.15
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; WikiBot/1.0)"}

session = requests.Session()
session.headers.update(HEADERS)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fetch(url: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=25)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            if attempt == retries - 1:
                print(f"[FAIL] {url}: {e}")
                return ""
            time.sleep(1.5)
    return ""


def parse_article(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    article = soup.find("article")
    if not article:
        article = soup.find("main") or soup.find("body")

    # Remove navigation / breadcrumbs / scripts inside article
    for tag in article.find_all(["nav", "script", "style", "footer"]):
        tag.decompose()
    for comment in article.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # Title: first h1 text
    h1 = article.find("h1")
    title = h1.get_text(strip=True) if h1 else Path(urlparse(url).path).name

    # Tags: links to /tags/
    tags = []
    for a in soup.find_all("a", href=re.compile(r"^/tags/|^\./tags/")):
        t = a.get_text(strip=True)
        if t and t not in tags:
            tags.append(t)

    # Backlinks section
    backlinks = []
    backlinks_header = None
    for header in article.find_all(["h2", "h3", "h4", "h5"]):
        txt = header.get_text(strip=True).lower()
        if "liên kết ngược" in txt or "backlinks" in txt:
            backlinks_header = header
            break

    if backlinks_header:
        nxt = backlinks_header.find_next_sibling()
        while nxt and nxt.name not in ("h2", "h3", "h4", "h5"):
            if nxt.name == "ul":
                for li in nxt.find_all("li"):
                    a = li.find("a")
                    if a:
                        backlinks.append(
                            {
                                "text": a.get_text(strip=True),
                                "href": a.get("href", ""),
                            }
                        )
            nxt = nxt.find_next_sibling()

    # Extract all internal links inside article (concepts, hubs, tags)
    related = []
    seen_rel = set()
    for a in article.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http") and not href.startswith(BASE_URL):
            continue
        if href.startswith("#"):
            continue
        abs_href = urljoin(url, href)
        if abs_href == url:
            continue
        if abs_href not in seen_rel:
            seen_rel.add(abs_href)
            related.append(
                {
                    "text": a.get_text(strip=True),
                    "href": href,
                    "abs": abs_href,
                }
            )

    # Convert article HTML -> Markdown
    md = markdownify.markdownify(str(article), heading_style="ATX")
    # Fix up relative links in markdown to absolute so downstream systems can resolve
    # markdownify keeps href as-is, which is fine for local obsidian-style usage.

    return {
        "title": title,
        "url": url,
        "tags": tags,
        "backlinks": backlinks,
        "related": related,
        "markdown": md,
    }


def save_page(data: dict, rel_path: str):
    if "/hubs/" in rel_path:
        subdir = OUTPUT_DIR / "hubs"
    elif "/concepts/" in rel_path:
        subdir = OUTPUT_DIR / "concepts"
    elif "/tags/" in rel_path:
        subdir = OUTPUT_DIR / "tags"
    else:
        subdir = OUTPUT_DIR

    slug = Path(rel_path).name or "index"
    if not slug.endswith(".md"):
        slug += ".md"

    filepath = subdir / slug

    frontmatter = {
        "title": data["title"],
        "source_url": data["url"],
        "tags": data["tags"],
        "backlinks": data["backlinks"],
        "related_count": len(data["related"]),
        "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    md = f"---\n{yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)}---\n\n"
    md += data["markdown"]
    filepath.write_text(md, encoding="utf-8")
    print(f"[SAVED] {filepath} ({len(data['markdown'])} chars)")


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_all_urls() -> set:
    """Parse index then do a limited BFS through hub/tag pages to discover every concept."""
    urls = set()
    to_crawl = [BASE_URL + "/"]
    crawled = set()

    while to_crawl:
        batch = to_crawl[:20]
        to_crawl = to_crawl[20:]
        for url in batch:
            if url in crawled:
                continue
            crawled.add(url)
            html = fetch(url)
            if not html:
                continue
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if any(
                    href.startswith(p)
                    for p in (
                        "/hubs/",
                        "/concepts/",
                        "/tags/",
                        "./hubs/",
                        "./concepts/",
                        "./tags/",
                    )
                ):
                    # Normalize
                    if href.startswith("."):
                        href = href[1:]  # remove leading dot
                    full = urljoin(BASE_URL, href)
                    # Remove fragment
                    full = full.split("#")[0]
                    if full not in crawled and full not in to_crawl:
                        to_crawl.append(full)
                        urls.add(full)
                elif href.startswith("/") and not href.startswith("//"):
                    # Could be root-relative concept/hub/tag not caught above
                    if any(
                        href.startswith(p) for p in ("/hubs/", "/concepts/", "/tags/")
                    ):
                        full = urljoin(BASE_URL, href).split("#")[0]
                        if full not in crawled and full not in to_crawl:
                            to_crawl.append(full)
                            urls.add(full)
            time.sleep(DELAY)

    urls.add(BASE_URL + "/")
    return urls


# ---------------------------------------------------------------------------
# Main crawl
# ---------------------------------------------------------------------------


def crawl_all():
    urls = discover_all_urls()
    urls = sorted(urls)
    print(f"\n[PLAN] Total URLs to crawl: {len(urls)}\n")

    results = []
    graph = {
        "nodes": [],
        "edges": [],
    }

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(fetch, url): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            html = future.result()
            if html:
                try:
                    data = parse_article(html, url)
                    rel = urlparse(url).path
                    save_page(data, rel)

                    node_id = rel.strip("/").replace("/", "_") or "index"
                    graph["nodes"].append(
                        {
                            "id": node_id,
                            "title": data["title"],
                            "url": url,
                            "type": (
                                "hub"
                                if "/hubs/" in rel
                                else ("tag" if "/tags/" in rel else "concept")
                            ),
                            "tags": data["tags"],
                        }
                    )
                    for r in data["related"]:
                        target_rel = (
                            urlparse(r["abs"]).path.strip("/").replace("/", "_")
                        )
                        if target_rel:
                            graph["edges"].append(
                                {
                                    "source": node_id,
                                    "target": target_rel,
                                    "label": r["text"],
                                }
                            )

                    results.append({"url": url, "status": "ok", "title": data["title"]})
                except Exception as e:
                    print(f"[PARSE ERROR] {url}: {e}")
                    results.append({"url": url, "status": "parse_error", "title": ""})
            else:
                results.append({"url": url, "status": "fail", "title": ""})
            time.sleep(DELAY)

    # Deduplicate edges
    seen_edges = set()
    unique_edges = []
    for e in graph["edges"]:
        key = (e["source"], e["target"], e["label"])
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(e)
    graph["edges"] = unique_edges

    # Save artifacts
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "graph.json").write_text(
        json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    ok = sum(1 for r in results if r["status"] == "ok")
    fail = len(results) - ok
    print(f"\n[DONE] OK: {ok} | FAIL: {fail} | TOTAL: {len(results)}")
    print(
        f"[ARTIFACTS] manifest.json | graph.json | {len(graph['nodes'])} nodes | {len(graph['edges'])} edges"
    )


if __name__ == "__main__":
    crawl_all()
