#!/usr/bin/env python3
# File: update_link_titles.py
#
# Dependencies:
#   - Python 3
#   - curl
#   - beautifulsoup4 → pip install beautifulsoup4
#
# Fetch and update Markdown link titles
#
# Arguments:
#   --all        Update every http/https link that has no title.
#   --overwrite  Update all http/https links, replacing existing titles.
#   (none)       Update only links whose name starts with "http" and have no title.
#
# Examples:
#   python3 update_link_titles.py file.md
#   python3 update_link_titles.py --all content/
#   python3 update_link_titles.py --overwrite /path/to/*.md

import os, sys, subprocess, html
from bs4 import BeautifulSoup

def fetch_page_title(url: str) -> str | None:
    try:
        html_data = subprocess.check_output(
            ["curl", "-Ls", url], stderr=subprocess.DEVNULL, timeout=12
        ).decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html_data, "html.parser")
        if soup.title and soup.title.string:
            return html.unescape(soup.title.string.strip())
        return None
    except Exception:
        return None

def should_update(text: str, has_title: bool, mode: str) -> bool:
    if mode == "overwrite":
        return True
    if mode == "http-only":
        if not text.startswith("http"):
            return False
        return not has_title
    if mode == "all":
        return not has_title
    return False

# Parser for Markdown links: finds [text](url "title")
def parse_links(md: str):
    i, n = 0, len(md)
    while i < n:
        if md[i] != '[':
            i += 1
            continue
        # Find closing ] for text
        j = i + 1
        while j < n and md[j] != ']':
            j += 1
        if j >= n or j + 1 >= n or md[j + 1] != '(':
            i += 1
            continue
        # Parse ( ... ) allowing nested parens in url
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
        url, title = None, None
        if '"' in block:
            q1 = block.find('"')
            q2 = block.rfind('"')
            if q2 > q1:
                url = block[:q1].strip()
                title = block[q1 + 1 : q2]
            else:
                url = block.strip()
        else:
            url = block
        text = md[i + 1 : j]
        yield (i, k, text, url, title)
        i = k

def print_summary(path: str,
                  total_candidates: int,
                  skipped_name_mode_count: int,
                  skipped_malformed: list,
                  skipped_empty_title: list,
                  skipped_fetch_error: list,
                  per_file_errors: list,
                  mode: str) -> None:
    # Header for each file
    print(f"{path}")
    print(f"  - {total_candidates} candidate titles to update")

    # Only list truly bad links (broken, empty title, fetch fail)
    if skipped_malformed:
        print(f"  - {len(skipped_malformed)} bad links (malformed):")
        for url in skipped_malformed:
            print(f"    - {url}")
    if skipped_empty_title:
        print(f"  - {len(skipped_empty_title)} links with no title:")
        for url in skipped_empty_title:
            print(f"    - {url}")
    if skipped_fetch_error:
        print(f"  - {len(skipped_fetch_error)} links failed to fetch:")
        for url in skipped_fetch_error:
            print(f"    - {url}")
    
    # Mode notes
    if skipped_name_mode_count:
        if mode == "http-only":
            print(f"  - {skipped_name_mode_count} skipped (non-http or already titled).")
            print(f"    Use --overwrite to force update, or run without flags to update missing ones.")
        elif mode == "all":
            print(f"  - {skipped_name_mode_count} skipped (already titled or invalid).")
            print(f"    Use --overwrite to force update.")
        elif mode == "overwrite":
            print(f"  - {skipped_name_mode_count} skipped even with --overwrite (invalid).")
        else:
            print(f"  - {skipped_name_mode_count} skipped (mode rules).")
            print(f"    Use --overwrite to force update.")

    # Per-link error lines (one per failed fetch)
    for err in per_file_errors:
        print(f"  - Error: {err}")

    print("")  # Empty line between files

def process_file(path: str, mode: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as file_handle:
            file_content = file_handle.read()
    except Exception:
        return

    parsed_links = list(parse_links(file_content))
    if not parsed_links:
        return

    # Buckets
    skipped_name_mode_count = 0             # Skipped because of name/mode rules (do not list URLs)
    skipped_malformed: list[str] = []       # Malformed or non-http URLs (list URLs)
    skipped_fetch_error: list[str] = []     # Curl errors or timeouts (list URLs)
    skipped_empty_title: list[str] = []     # Pages with empty title (list URLs)
    per_file_errors: list[str] = []

    candidates: list[tuple[int, int, str, str, str | None]] = []

    for (start_index, end_index, link_text, link_url, link_title) in parsed_links:
        if not link_url:
            skipped_malformed.append(f"{link_text or '<no-name>'} (no url)")
            continue
        if not link_url.startswith("http"):
            # Treat non-http as malformed for processing purposes
            skipped_malformed.append(link_url)
            continue
        if not should_update(link_text, link_title is not None, mode):
            skipped_name_mode_count += 1
            continue
        candidates.append((start_index, end_index, link_text, link_url, link_title))

    total_candidates = len(candidates)

    # If no candidates, print summary and return
    if total_candidates == 0:
        print_summary(path, total_candidates, skipped_name_mode_count, skipped_malformed, skipped_empty_title, skipped_fetch_error, per_file_errors, mode)
        return

    # Otherwise: print progress header and process candidates
    print(f"- {path}")
    print(f"  - 0/{total_candidates} processed")
    edits: list[tuple[int, int, str]] = []
    processed = 0

    for (start_index, end_index, link_text, link_url, link_title) in candidates:
        fetched_title = fetch_page_title(link_url)
        if fetched_title is None:
            skipped_fetch_error.append(link_url)
            per_file_errors.append(f"Failed to fetch title for {link_url}")
        elif not fetched_title.strip():
            skipped_empty_title.append(link_url)
        else:
            safe_title = html.unescape(fetched_title)
            rebuilt_link = f'[{link_text}]({link_url} "{safe_title}")'
            edits.append((start_index, end_index, rebuilt_link))
        processed += 1
        
        print(f"  - {processed} of {total_candidates} processed")

    # After processing candidates, print consolidated summary
    print_summary(path, total_candidates, skipped_name_mode_count, skipped_malformed, skipped_empty_title, skipped_fetch_error, per_file_errors, mode)

    if not edits:
        return

    # Apply edits from end to start to keep indices valid
    output_chunks: list[str] = []
    last_index = len(file_content)
    for start_index, end_index, rebuilt_link in reversed(edits):
        output_chunks.append(file_content[end_index:last_index])
        output_chunks.append(rebuilt_link)
        last_index = start_index
    output_chunks.append(file_content[:last_index])
    new_file_content = "".join(reversed(output_chunks))

    try:
        with open(path, "w", encoding="utf-8") as file_handle:
            file_handle.write(new_file_content)
    except Exception:
        pass

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
    print("")
    targets = args if args else ["."]
    for t in targets:
        walk_path(t, mode)

if __name__ == "__main__":
    main(sys.argv[1:])
