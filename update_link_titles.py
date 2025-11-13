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
#   --text-is-url            Update links whose text is a URL, even if no URL in link text.
#   --update-existing-titles Update all http/https links, replacing existing titles.
#   (none)                   Update every http/https link that has no title.
#
# Examples:
#   python3 update_link_titles.py file.md
#   python3 update_link_titles.py --text-is-url content/
#   python3 update_link_titles.py --update-existing-titles /path/to/*.md

import os
import sys
import subprocess
import html
from typing import Iterator, Tuple, List, Optional
from bs4 import BeautifulSoup

def fetch_page_title(url: str) -> Optional[str]:
    try:
        html_data = subprocess.check_output(
            [
                "curl",
                "-Ls",
                "-H",
                "Accept-Language: en",
                "--compressed",
                url,
            ],
            stderr=subprocess.DEVNULL,
            timeout=12,
        ).decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html_data, "html.parser")
        if soup.title and soup.title.string:
            return html.unescape(soup.title.string.strip())
        return None
    except Exception:
        return None

def should_update(text: str, has_title: bool, mode: str) -> bool:
    if mode == "update-existing-titles":
        return True
    if mode == "text-is-url":
        if not text.startswith("http"):
            return False
        return not has_title
    if mode == "all":
        return not has_title
    return False

# Parser for Markdown links: finds [text](url "title")
def parse_links(markdown_text: str) -> Iterator[Tuple[int, int, str, Optional[str], Optional[str]]]:
    # Scan the text to find Markdown link patterns: [text](url "title")
    pos, text_length = 0, len(markdown_text)

    while pos < text_length:
        # Look for the opening square bracket of the link text.
        if markdown_text[pos] != "[":
            pos += 1
            continue

        # Find the closing square bracket for the link text.
        end_bracket_index = pos + 1
        while end_bracket_index < text_length and markdown_text[end_bracket_index] != "]":
            end_bracket_index += 1

        # Confirm there is an opening parenthesis immediately after the closing bracket.
        if (
            end_bracket_index >= text_length
            or end_bracket_index + 1 >= text_length
            or markdown_text[end_bracket_index + 1] != "("
        ):
            pos += 1
            continue

        # Walk forward to find the matching closing parenthesis, supporting nested parentheses.
        end_parenthesis_index = end_bracket_index + 2
        parenthesis_depth = 1
        while end_parenthesis_index < text_length and parenthesis_depth > 0:
            current_character = markdown_text[end_parenthesis_index]
            if current_character == "(":
                parenthesis_depth += 1
            elif current_character == ")":
                parenthesis_depth -= 1
            end_parenthesis_index += 1

        # If parentheses are not balanced, skip this bracket and continue scanning.
        if parenthesis_depth != 0:
            pos += 1
            continue

        # Extract the content inside parentheses: `url "title"` or just `url`.
        link_block_text = markdown_text[end_bracket_index + 2 : end_parenthesis_index - 1].strip()
        link_url, link_title = None, None

        # Split URL and optional title by the outermost quotes.
        if '"' in link_block_text:
            quote_start_index = link_block_text.find('"')
            quote_end_index = link_block_text.rfind('"')
            if quote_end_index > quote_start_index:
                link_url = link_block_text[:quote_start_index].strip()
                link_title = link_block_text[quote_start_index + 1 : quote_end_index]
            else:
                link_url = link_block_text.strip()
        else:
            link_url = link_block_text

        # Extract the link text within brackets.
        link_text = markdown_text[pos + 1 : end_bracket_index]

        # Yield the span and parts: start index, end index, text, url, title.
        yield (pos, end_parenthesis_index, link_text, link_url, link_title)

        # Continue scanning after the closing parenthesis of the current link.
        pos = end_parenthesis_index

def print_summary(
    path: str,
    total_candidates: int,
    skipped_name_mode_count: int,
    skipped_malformed: List[str],
    skipped_empty_title: List[str],
    skipped_fetch_error: List[str],
    mode: str,
) -> None:
    print(f"{path}")
    print(f"  - Candidates to update: {total_candidates}")

    if skipped_malformed:
        print(f"  - Malformed: {len(skipped_malformed)}")
        for url in skipped_malformed:
            print(f"    - {url}")
    if skipped_empty_title:
        print(f"  - Empty titles: {len(skipped_empty_title)}")
        for url in skipped_empty_title:
            print(f"    - {url}")
    if skipped_fetch_error:
        print(f"  - Fetch failures: {len(skipped_fetch_error)}")
        for url in skipped_fetch_error:
            print(f"    - {url}")

    if skipped_name_mode_count:
        if mode == "text-is-url":
            print(f"  - Skipped by mode: {skipped_name_mode_count} — No URLs in the text of links or already titled.")
            print(f"    Use --update-existing-titles to force update.")
        elif mode == "all":
            print(f"  - Skipped by mode: {skipped_name_mode_count} — Already titled or invalid.")
            print(f"    Use --update-existing-titles to force update.")
        elif mode == "update-existing-titles":
            print(f"  - Skipped by mode: {skipped_name_mode_count} — Invalid.")
        else:
            print(f"  - Skipped by mode: {skipped_name_mode_count} — Mode rules.")
            print(f"    Use --update-existing-titles to force update.")

    print("")

def process_file(path: str, mode: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as file_handle:
            file_content = file_handle.read()
    except Exception:
        return

    parsed_links = list(parse_links(file_content))
    if not parsed_links:
        return

    skipped_name_mode_count = 0
    skipped_malformed: List[str] = []
    skipped_fetch_error: List[str] = []
    skipped_empty_title: List[str] = []

    candidates: List[Tuple[int, int, str, str, Optional[str]]] = []

    for (start_index, end_index, link_text, link_url, link_title) in parsed_links:
        if not link_url:
            skipped_malformed.append(f"{link_text or '<no-name>'} (no url)")
            continue
        # Skip silently:
        if (
            ("{{" in link_url and "}}" in link_url)
            or link_url.strip().startswith("{{<") # Hugo shortcodes – Standard notation
            or link_url.strip().startswith("{{%") # Hugo shortcodes – Markdown notation
            or link_url.strip().startswith("#") # Fragment-only URLs
        ):
            continue
        if not link_url.startswith("http"):
            skipped_malformed.append(link_url)
            continue
        if not should_update(link_text, link_title is not None, mode):
            skipped_name_mode_count += 1
            continue
        candidates.append((start_index, end_index, link_text, link_url, link_title))

    total_candidates = len(candidates)

    if total_candidates == 0:
        print_summary(path, total_candidates, skipped_name_mode_count, skipped_malformed, skipped_empty_title, skipped_fetch_error, mode)
        return

    processed = 0
    edits: List[Tuple[int, int, str]] = []

    # Single progress line that updates in place
    print(f"- {path}  {processed}/{total_candidates} processed", end="\r", flush=True)

    for (start_index, end_index, link_text, link_url, link_title) in candidates:
        fetched_title = fetch_page_title(link_url)
        if fetched_title is None:
            skipped_fetch_error.append(link_url)
        elif not fetched_title.strip():
            skipped_empty_title.append(link_url)
        else:
            safe_title = html.unescape(fetched_title)
            rebuilt_link = f'[{link_text}]({link_url} "{safe_title}")'
            edits.append((start_index, end_index, rebuilt_link))
        processed += 1
        print(f"- {path}  {processed}/{total_candidates} processed", end="\r", flush=True)

    # Finish progress line with newline
    print("")

    print_summary(path, total_candidates, skipped_name_mode_count, skipped_malformed, skipped_empty_title, skipped_fetch_error, mode)

    if not edits:
        return

    output_chunks: List[str] = []
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

def main(argument_values: List[str]) -> None:
    mode = "all"
    args = [a for a in argument_values if not a.startswith("--")]
    if "--text-is-url" in argument_values:
        mode = "text-is-url"
    if "--update-existing-titles" in argument_values:
        mode = "update-existing-titles"
    targets = args if args else ["."]
    for t in targets:
        walk_path(t, mode)

if __name__ == "__main__":
    main(sys.argv[1:])
