#!/usr/bin/env python3
# File: update_link_titles.py
#
# Dependencies:
#   - Python 3
#   - curl
#   - beautifulsoup4 → pip install beautifulsoup4
#
# Fetch and update Markdown link titles: [text](url "title") or [text](url 'title')
#
# Arguments:
#   --text-is-url            Update links whose text is a URL, even if no URL in link text.
#   --update-existing-titles Update all http/https links, replacing existing titles.
#   --lang=cs                Set preferred language for the link scraper and cache, default: en
#   --stash                  Stash existing titles into cache and remove them from Markdown.
#   (none)                   Update every http/https link that has no title.
#
# Examples:
#   python3 update_link_titles.py profiles.md
#   python3 update_link_titles.py --text-is-url content/
#   python3 update_link_titles.py --update-existing-titles content/en/posts/*.md
#   python3 update_link_titles.py --lang=cs content/cs/posts/*.md
#   python3 update_link_titles.py --stash content/

# The user will be warned about potentially broken links:
SUSPICIOUS_TITLE_PATTERNS = [
    r"^\s+?- YouTube",
    r"Verify.+Human",
    r"(please wait|just a moment)",
    r"(404|not found)",
]

CACHE_FILENAME = "update_link_titles_cache"

import html
import json
import os
import re
import subprocess
import sys
from bs4 import BeautifulSoup
from typing import Iterator, Tuple, List, Optional, Dict

def get_cache_path(lang: str) -> str:
    suffix = "" if lang == "en" else f"-{lang}"
    return f"{CACHE_FILENAME}{suffix}.json"

def load_cache(lang: str) -> Dict[str, str]:
    path = get_cache_path(lang)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_cache(cache: Dict[str, str], lang: str) -> None:
    path = get_cache_path(lang)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False, sort_keys=True)
            f.write("\n")
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")

def normalize_url(url: str) -> str:
    # Remove fragment
    url = url.split("#")[0]
    # Remove trailing slash
    if url.endswith("/"):
        url = url[:-1]
    # Normalize protocol (https->http) and remove www
    return re.sub(r"^https?://(?:www\.)?", "http://", url, flags=re.IGNORECASE)

def fetch_page_title(url: str, lang: str) -> Optional[str]:
    try:
        html_data = subprocess.check_output(
            [
                "curl",
                "-Ls",
                "-H",
                f"Accept-Language: {lang}",
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

# Parser for Markdown links: finds [text](url "title") or [text](url 'title')
def parse_links(markdown_text: str) -> Iterator[Tuple[int, int, str, Optional[str], Optional[str]]]:
    # Scan the text to find Markdown link patterns: [text](url "title") or [text](url 'title')
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

        # Extract the content inside parentheses: `url "title"` or `url 'title'` or just `url`.
        link_block_text = markdown_text[end_bracket_index + 2 : end_parenthesis_index - 1].strip()
        link_url, link_title = None, None

        # Split URL and optional title by the outermost matching quote (single or double).
        quote_start_index = None
        quote_char = None
        for i, ch in enumerate(link_block_text):
            if ch == '"' or ch == "'":
                quote_start_index = i
                quote_char = ch
                break

        if quote_start_index is not None:
            quote_end_index = link_block_text.rfind(quote_char)
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

def is_suspicious_title(title_text: str) -> bool:
    for pattern in SUSPICIOUS_TITLE_PATTERNS:
        if re.search(pattern, title_text, re.IGNORECASE):
            return True
    return False

def print_summary(
    path: str,
    total_candidates: int,
    skipped_name_mode_count: int,
    skipped_malformed: List[str],
    skipped_empty_title: List[str],
    skipped_fetch_error: List[str],
    suspicious_title_warnings: List[str],
    mode: str,
) -> None:
    print(f"{path}")

    has_processing_issues = (
        len(skipped_malformed) > 0
        or len(skipped_empty_title) > 0
        or len(skipped_fetch_error) > 0
        or len(suspicious_title_warnings) > 0
    )

    if has_processing_issues or mode == "stash":
        print(f"  - Links processed: {total_candidates}")

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
            
    # These were updated, but we warn the user to check them
    if suspicious_title_warnings:
        print(f"  - Suspicious titles: {len(suspicious_title_warnings)}")
        for title in suspicious_title_warnings:
            print(f"    - \"{title}\"")

    if skipped_name_mode_count:
        if mode == "text-is-url":
            print(f"  - Skipped {skipped_name_mode_count} links – no URLs in the text or already titled.")
            print(f"    Use --update-existing-titles to force update.")
        elif mode == "all":
            print(f"  - Skipped {skipped_name_mode_count} links – already titled.")
            print(f"    Use --update-existing-titles to force update.")
        elif mode == "update-existing-titles":
            print(f"  - Skipped {skipped_name_mode_count} invalid links.")
        elif mode == "stash":
            print(f"  - Skipped {skipped_name_mode_count} links – no title to stash.")
        else:
            print(f"  - Skipped {skipped_name_mode_count} links due to mode rules.")
            print(f"    Use --update-existing-titles to force update.")

    print("")

def format_link_title_for_markdown(raw_title: str) -> str:
    title = html.unescape(raw_title.strip())

    # Prefer single-quote delimiter if no single quote inside
    if "'" not in title:
        return f"'{title}'"

    # Else prefer double-quote delimiter if no double quote inside
    if '"' not in title:
        return f'"{title}"'

    # Both quote types present — worst case: drop double quotes, wrap in double quotes
    title_without_double = title.replace('"', "")
    return f'"{title_without_double}"'

def process_file(path: str, mode: str, lang: str, cache: Dict[str, str]) -> None:
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
    suspicious_title_warnings: List[str] = []

    candidates: List[Tuple[int, int, str, str, Optional[str]]] = []
    edits: List[Tuple[int, int, str]] = []

    for (start_index, end_index, link_text, link_url, link_title) in parsed_links:
        if not link_url:
            skipped_malformed.append(f"{link_text or '<no-name>'} (no url)")
            continue
        # Skip silently (ignore):
        if (
            ("{{" in link_url and "}}" in link_url)
            or link_url.strip().startswith("{{<") # Hugo shortcodes – Standard notation
            or link_url.strip().startswith("{{%") # Hugo shortcodes – Markdown notation
            or link_url.strip().startswith("#") # Fragment-only URLs
            or link_url.strip().startswith("x-apple.systempreferences:") # macOS System Settings URLs
        ):
            continue
        if not link_url.startswith("http"):
            skipped_malformed.append(link_url)
            continue
        
        if mode == "stash":
            # In stash mode, we only process links that HAVE a title
            if link_title:
                candidates.append((start_index, end_index, link_text, link_url, link_title))
            else:
                skipped_name_mode_count += 1
        else:
            if not should_update(link_text, link_title is not None, mode):
                skipped_name_mode_count += 1
                continue
            candidates.append((start_index, end_index, link_text, link_url, link_title))

    total_candidates = len(candidates)

    if total_candidates == 0:
        print_summary(path, total_candidates, skipped_name_mode_count, skipped_malformed, skipped_empty_title, skipped_fetch_error, suspicious_title_warnings, mode)
        return

    processed = 0
    # Single progress line that updates in place
    print(f"{path}  {processed}/{total_candidates} processed", end="\r", flush=True)

    for (start_index, end_index, link_text, link_url, link_title) in candidates:
        norm_url = normalize_url(link_url)

        if mode == "stash":
            # Extract title to cache
            if link_title and link_title.strip():
                clean_title = html.unescape(link_title.strip())
                if not is_suspicious_title(clean_title):
                    cache[norm_url] = clean_title
            
            # Remove title from file
            rebuilt_link = f'[{link_text}]({link_url})'
            edits.append((start_index, end_index, rebuilt_link))
        
        else:
            # Update/Fetch mode
            # Try cache first
            if norm_url in cache:
                fetched_title = cache[norm_url]
            else:
                fetched_title = fetch_page_title(link_url, lang)
                if fetched_title and fetched_title.strip() and not is_suspicious_title(fetched_title):
                    cache[norm_url] = fetched_title

            if fetched_title is None:
                skipped_fetch_error.append(link_url)
            elif not fetched_title.strip():
                skipped_empty_title.append(link_url)
            else:
                # Check for suspicious titles, warn but proceed with update
                if is_suspicious_title(fetched_title):
                    suspicious_title_warnings.append(fetched_title)

                formatted_title = format_link_title_for_markdown(fetched_title)
                rebuilt_link = f'[{link_text}]({link_url} {formatted_title})'
                edits.append((start_index, end_index, rebuilt_link))
        
        processed += 1
        print(f"{path}  {processed}/{total_candidates} processed", end="\r", flush=True)

    # Finish progress line with newline
    print("")

    print_summary(path, total_candidates, skipped_name_mode_count, skipped_malformed, skipped_empty_title, skipped_fetch_error, suspicious_title_warnings, mode)

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

def walk_path(path: str, mode: str, lang: str, cache: Dict[str, str]) -> None:
    if os.path.isfile(path):
        if path.endswith(".md"):
            process_file(path, mode, lang, cache)
        return
    for root, _, files in os.walk(path):
        for name in files:
            if name.endswith(".md"):
                process_file(os.path.join(root, name), mode, lang, cache)

def main(argument_values: List[str]) -> None:
    mode = "all"
    lang = "en"

    args: List[str] = []
    for argument in argument_values:
        if argument == "--text-is-url":
            mode = "text-is-url"
            continue
        if argument == "--update-existing-titles":
            mode = "update-existing-titles"
            continue
        if argument == "--stash":
            mode = "stash"
            continue
        if argument.startswith("--lang="):
            lang = argument.split("=", 1)[1]
            continue
        if not argument.startswith("--"):
            args.append(argument)

    # Load cache
    cache = load_cache(lang)

    targets = args if args else ["."]
    try:
        for target in targets:
            walk_path(target, mode, lang, cache)
    finally:
        # Save cache
        save_cache(cache, lang)

if __name__ == "__main__":
    main(sys.argv[1:])