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
#   python3 update_link_titles.py --stash content/en && python3 update_link_titles.py --stash --lang=cs content/cs
#   python3 update_link_titles.py content/en/ && python3 update_link_titles.py --lang=cs content/cs/

import html
import json
import os
import re
import subprocess
import sys
from bs4 import BeautifulSoup
from typing import Iterator, Tuple, List, Optional, Dict

# The user will be warned about potentially broken links:
SUSPICIOUS_TITLE_PATTERNS = [
    r"^(\s+)?(- )?YouTube$",
    r"Verify.+Human",
    r"(please wait|just a moment|captcha)",
    r"(404|not found)",
]

CACHE_DIR = "resources/_gen/"
CACHE_FILENAME = "update_link_titles_cache"


def get_cache_path(lang: str) -> str:
    suffix = "" if lang == "en" else f"-{lang}"
    return f"{CACHE_DIR}{CACHE_FILENAME}{suffix}.json"


def load_cache(lang: str) -> Dict[str, str]:
    path = get_cache_path(lang)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_cache(cache: Dict[str, str], lang: str) -> None:
    path = get_cache_path(lang)
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(cache, file, indent=2, ensure_ascii=False, sort_keys=True)
            file.write("\n")
    except Exception as error:
        print(f"Warning: Could not save cache: {error}")


def normalize_url(url: str) -> str:
    url = url.split("#")[0]
    if url.endswith("/"):
        url = url[:-1]
    return re.sub(r"^https?://(?:www\.)?", "http://", url, flags=re.IGNORECASE)


def fetch_page_title(url: str, lang: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        process = subprocess.run(
            [
                "curl",
                "-Ls",
                "-H",
                f"Accept-Language: {lang}",
                "--compressed",
                "-w",
                "%{http_code}",
                url,
            ],
            capture_output=True,
            timeout=12,
        )
        
        if process.returncode != 0:
            return None, f"curl error {process.returncode}"
            
        output = process.stdout.decode("utf-8", errors="ignore")
        if len(output) < 3:
            return None, "empty response"
            
        # Extract http code from the end of stdout
        http_code = output[-3:]
        html_content = output[:-3]
        
        if http_code.startswith(("4", "5")):
            return None, f"HTTP {http_code}"
            
        soup = BeautifulSoup(html_content, "html.parser")
        if soup.title and soup.title.string:
            return html.unescape(soup.title.string.strip()), None
        return None, None
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except Exception as error:
        return None, "system error"


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
    pos, char_count = 0, len(markdown_text)

    while pos < char_count:
        # Look for the opening square bracket of the link text.
        if markdown_text[pos] != "[":
            pos += 1
            continue

        # Find the closing square bracket for the link text.
        end_bracket_index = pos + 1
        while end_bracket_index < char_count and markdown_text[end_bracket_index] != "]":
            end_bracket_index += 1

        # Confirm there is an opening parenthesis immediately after the closing bracket.
        if (
            end_bracket_index >= char_count
            or end_bracket_index + 1 >= char_count
            or markdown_text[end_bracket_index + 1] != "("
        ):
            pos += 1
            continue

        # Walk forward to find the matching closing parenthesis, supporting nested parentheses.
        end_parenthesis_index = end_bracket_index + 2
        parenthesis_depth = 1
        while end_parenthesis_index < char_count and parenthesis_depth > 0:
            char = markdown_text[end_parenthesis_index]
            if char == "(":
                parenthesis_depth += 1
            elif char == ")":
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
        for index, char in enumerate(link_block_text):
            if char == '"' or char == "'":
                quote_start_index = index
                quote_char = char
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
    candidate_count: int,
    skipped_mode_count: int,
    skipped_malformed: List[str],
    skipped_empty_title: List[str],
    skipped_fetch_error: List[str],
    suspicious_title_warnings: List[str],
    mode: str,
) -> None:
    has_messages = bool(
        skipped_malformed
        or skipped_empty_title
        or skipped_fetch_error
        or suspicious_title_warnings
        or skipped_mode_count
    )

    if has_messages:
        if candidate_count > 0:
            print(f"{path} {candidate_count}/{candidate_count} processed")
        else:
            print(f"{path}")

        if skipped_malformed:
            print(f"  - Malformed: {len(skipped_malformed)}")
            for url in skipped_malformed:
                print(f"    - {url}")
        if skipped_empty_title:
            print(f"  - Empty titles: {len(skipped_empty_title)}")
            for url in skipped_empty_title:
                print(f"    - {url}")
        if skipped_fetch_error:
            print(f"  - Fetch errors and dead URLs: {len(skipped_fetch_error)}")
            for url in skipped_fetch_error:
                print(f"    - {url}")
                
        # These were updated, but we warn the user to check them
        if suspicious_title_warnings:
            print(f"  - Suspicious titles: {len(suspicious_title_warnings)}")
            for title in suspicious_title_warnings:
                print(f"    - \"{title}\"")

        if skipped_mode_count:
            if mode == "text-is-url":
                print(f"  - Skipped {skipped_mode_count} links – no URLs in the text or already titled")
            elif mode == "all":
                print(f"  - Skipped {skipped_mode_count} links – already titled")
            elif mode == "update-existing-titles":
                print(f"  - Skipped {skipped_mode_count} invalid links")
            elif mode == "stash":
                print(f"  - Skipped {skipped_mode_count} links – no title to stash")
            else:
                print(f"  - Skipped {skipped_mode_count} links due to mode rules")


def format_link_title_for_markdown(raw_title: str) -> str:
    title = html.unescape(raw_title.strip())

    if "'" not in title:
        return f"'{title}'"

    if '"' not in title:
        return f'"{title}"'

    title_without_double = title.replace('"', "")
    return f'"{title_without_double}"'


def process_file(path: str, mode: str, lang: str, cache: Dict[str, str]) -> int:
    try:
        with open(path, "r", encoding="utf-8") as file:
            file_content = file.read()
    except Exception:
        return 0

    parsed_links = list(parse_links(file_content))
    if not parsed_links:
        return 0

    skipped_mode_count = 0
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
            or link_url.strip().startswith("imessage:") # iMessage
            or link_url.strip().endswith(".vcf") # File (.vcf)
        ):
            continue
            
        if not link_url.startswith("http"):
            skipped_malformed.append(link_url)
            continue
        
        if mode == "stash":
            if link_title:
                candidates.append((start_index, end_index, link_text, link_url, link_title))
            else:
                skipped_mode_count += 1
        else:
            if not should_update(link_text, link_title is not None, mode):
                skipped_mode_count += 1
                continue
            candidates.append((start_index, end_index, link_text, link_url, link_title))

    candidate_count = len(candidates)

    if candidate_count == 0:
        print_summary(path, candidate_count, skipped_mode_count, skipped_malformed, skipped_empty_title, skipped_fetch_error, suspicious_title_warnings, mode)
        return skipped_mode_count

    processed_count = 0
    print(f"{path} {processed_count}/{candidate_count} processed", end="\r", flush=True)

    for (start_index, end_index, link_text, link_url, link_title) in candidates:
        normalized_url = normalize_url(link_url)

        if mode == "stash":
            if link_title and link_title.strip():
                clean_title = html.unescape(link_title.strip())
                if not is_suspicious_title(clean_title):
                    cache[normalized_url] = clean_title
            
            rebuilt_link = f'[{link_text}]({link_url})'
            edits.append((start_index, end_index, rebuilt_link))
        
        else:
            fetch_error = None
            if normalized_url in cache:
                fetched_title = cache[normalized_url]
            else:
                fetched_title, fetch_error = fetch_page_title(link_url, lang)
                if fetched_title and fetched_title.strip() and not is_suspicious_title(fetched_title):
                    cache[normalized_url] = fetched_title

            if fetch_error:
                skipped_fetch_error.append(f"{link_url} [{fetch_error}]")
            elif fetched_title is None:
                skipped_fetch_error.append(link_url)
            elif not fetched_title.strip():
                skipped_empty_title.append(link_url)
            else:
                if is_suspicious_title(fetched_title):
                    suspicious_title_warnings.append(fetched_title)

                formatted_title = format_link_title_for_markdown(fetched_title)
                rebuilt_link = f'[{link_text}]({link_url} {formatted_title})'
                edits.append((start_index, end_index, rebuilt_link))
        
        processed_count += 1
        print(f"{path} {processed_count}/{candidate_count} processed", end="\r", flush=True)

    # Finish progress line with newline
    print("")

    print_summary(path, candidate_count, skipped_mode_count, skipped_malformed, skipped_empty_title, skipped_fetch_error, suspicious_title_warnings, mode)

    if not edits:
        return skipped_mode_count

    output_chunks: List[str] = []
    last_index = len(file_content)
    
    # Apply changes from bottom to top to preserve string indices
    for start_index, end_index, rebuilt_link in reversed(edits):
        output_chunks.append(file_content[end_index:last_index])
        output_chunks.append(rebuilt_link)
        last_index = start_index
    output_chunks.append(file_content[:last_index])
    new_file_content = "".join(reversed(output_chunks))

    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(new_file_content)
    except Exception:
        pass

    return skipped_mode_count


def walk_path(path: str, mode: str, lang: str, cache: Dict[str, str]) -> int:
    skipped_count = 0
    if os.path.isfile(path):
        if path.endswith(".md"):
            skipped_count += process_file(path, mode, lang, cache)
        return skipped_count
        
    for root, _, files in os.walk(path):
        for name in files:
            if name.endswith(".md"):
                skipped_count += process_file(os.path.join(root, name), mode, lang, cache)
                
    return skipped_count


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

    cache = {} if mode == "stash" else load_cache(lang)
    targets = args if args else ["."]
    skipped_link_count = 0
    
    try:
        for target in targets:
            skipped_link_count += walk_path(target, mode, lang, cache)
    finally:
        save_cache(cache, lang)

    if skipped_link_count > 0 and mode not in ("update-existing-titles", "stash"):
        print("\nUse --update-existing-titles to force update skipped links.")


if __name__ == "__main__":
    main(sys.argv[1:])