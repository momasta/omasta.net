#!/usr/bin/env python3
# File: update_link_titles.py
#
# Dependencies:
#   • Python 3
#   • curl
#   • beautifulsoup4  →  pip install beautifulsoup4
#
# Usage:
#   python3 update_link_titles.py content/file.md
#   python3 update_link_titles.py content/*/posts
#   python3 update_link_titles.py content/dir --all
#   python3 update_link_titles.py content/dir --overwrite
#   python3 update_link_titles.py                 # current dir, http-only, skip described

import os, sys, subprocess, html
from bs4 import BeautifulSoup

def fetch_page_title(url: str) -> str | None:
    try:
        html_data = subprocess.check_output(
            ["curl", "-Ls", url], stderr=subprocess.DEVNULL, timeout=12
        ).decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html_data, "html.parser")
        return (soup.title.string or "").strip() if soup.title else None
    except Exception:
        return None

def should_update(label: str, has_desc: bool, mode: str) -> bool:
    if mode == "overwrite": return True
    if mode == "http-only":
        if not label.startswith("http"): return False
        return not has_desc
    if mode == "all": return True
    return False

# Non-regex Markdown link parser: finds [label](url "desc")
def parse_links(md: str):
    i, n = 0, len(md)
    while i < n:
        if md[i] != '[':
            i += 1
            continue
        # find closing ] for label
        j = i + 1
        while j < n and md[j] != ']':
            j += 1
        if j >= n or j + 1 >= n or md[j + 1] != '(':
            i += 1
            continue
        # parse ( ... ) allowing nested parens in url
        k = j + 2
        depth = 1
        while k < n and depth > 0:
            ch = md[k]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            k += 1
        if depth != 0:
            i += 1
            continue
        block = md[j + 2 : k - 1].strip()
        url, desc = None, None
        if '"' in block:
            q1 = block.find('"')
            q2 = block.rfind('"')
            if q2 > q1:
                url = block[:q1].strip()
                desc = block[q1 + 1 : q2]
            else:
                url = block.strip()
        else:
            url = block
        label = md[i + 1 : j]
        yield (i, k, label, url, desc)
        i = k

def process_file(path: str, mode: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return

    links = list(parse_links(content))
    total = len(links)
    if total == 0:
        return

    print(f"Processing {path} ... 0/{total}", end="", flush=True)
    edits = []
    done = 0

    for (s, e, label, url, desc) in links:
        if not url or not url.startswith("http"):
            done += 1
            print(f"\rProcessing {path} ... {done}/{total}", end="", flush=True)
            continue
        if not should_update(label, desc is not None, mode):
            done += 1
            print(f"\rProcessing {path} ... {done}/{total}", end="", flush=True)
            continue
        new_desc = fetch_page_title(url)
        if new_desc:
            safe_desc = html.escape(new_desc, quote=True)
            rebuilt = f'[{label}]({url} "{safe_desc}")'
            edits.append((s, e, rebuilt))
        done += 1
        print(f"\rProcessing {path} ... {done}/{total}", end="", flush=True)

    if not edits:
        print("")  # newline after progress line
        return

    # Apply edits from end to start to keep indices valid
    out = []
    last = len(content)
    for s, e, rebuilt in reversed(edits):
        out.append(content[e:last])
        out.append(rebuilt)
        last = s
    out.append(content[:last])
    new_content = "".join(reversed(out))

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception:
        pass
    print("")

def walk_path(path: str, mode: str) -> None:
    if os.path.isfile(path):
        if path.endswith(".md"):
            process_file(path, mode)
        return
    for root, _, files in os.walk(path):
        for name in files:
            if name.endswith(".md"):
                process_file(os.path.join(root, name), mode)

def main(argv: list[str]) -> None:
    mode = "http-only"
    args = [a for a in argv if not a.startswith("--")]
    if "--all" in argv: mode = "all"
    if "--overwrite" in argv: mode = "overwrite"
    targets = args if args else ["."]
    for t in targets:
        walk_path(t, mode)

if __name__ == "__main__":
    main(sys.argv[1:])
