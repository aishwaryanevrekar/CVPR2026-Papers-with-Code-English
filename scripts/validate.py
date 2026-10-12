#!/usr/bin/env python3
"""Validate the English CVPR 2026 collection; optionally compare an upstream copy.

Uses the repository's inline Markdown links and HTML anchors, not a full Markdown
parser. Checks local destinations but does not request external URLs.
"""

import argparse
from collections import Counter
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
CJK = re.compile(r"[\u3400-\u9fff\uf900-\ufaff\U00020000-\U0002fa1f]")
LINK = re.compile(r"!?\[([^\]\n]*)\]\((<[^>\n]+>|[^\s)]+)(?:\s+[\"'][^\n]*?[\"'])?\)")
URL = re.compile(r"https?://[^\s<>\"\[\]{}()\u3000-\u303f\uff00-\uffef]+")
ANCHOR = re.compile(r"<a\b[^>]*\b(?:id|name)\s*=\s*['\"]([^'\"]+)['\"][^>]*>", re.I)
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.M)
LABEL = re.compile(
    r"^\s*[-*]\s*(?:Paper|Code|Project|Project Page|Homepage|Home|GitHub|"
    r"Dataset|Demo|Demo Video|Model|Affiliations|Commentary|Evaluation Toolkit)"
    r"(?:\s+and\s+(?:Dataset|Code))?(?:\s*\([^)]*\))?\s*[:：]\s*(.*?)\s*$",
    re.I,
)


def anchors(text):
    """Include explicit anchors and GitHub-style heading IDs for simple headings."""
    result = set(ANCHOR.findall(text))
    seen = Counter()
    for heading in HEADING.findall(text):
        heading = LINK.sub(lambda match: match[1], heading)
        slug = re.sub(r"[^\w\s-]", "", heading.lower()).replace(" ", "-")
        result.add(slug if not seen[slug] else f"{slug}-{seen[slug]}")
        seen[slug] += 1
    return result


def external_urls(text):
    # Link text is presentation; only the actual destination counts as a URL.
    text = LINK.sub(lambda match: " " + match[2].strip("<>") + " ", text)
    return Counter(match.rstrip(".,;:!?") for match in URL.findall(text))


def paper_titles(text):
    """Read title text before resource lists, including unbolded source titles."""
    first = ANCHOR.search(text)
    if first is None:
        return Counter()
    titles = []
    pending = []
    for line in text[first.end():].splitlines():
        line = line.strip()
        if not line or not line.strip("* "):
            continue
        if line.startswith("#") or ANCHOR.search(line):
            pending = []
        elif re.match(r"^- (?:Paper|Code|Project|Model):", line):
            if pending:
                title = " ".join(pending)
                if not CJK.search(title):
                    titles.append(title)
                pending = []
        else:
            pending.append(line.strip("* "))
    return Counter(titles)


def paper_resources(text):
    """Compare the paper sections, excluding editorial and promotional links."""
    first = ANCHOR.search(text)
    return external_urls(text[first.end():]) if first else Counter()


def validate(upstream=None):
    errors = []
    readme = ROOT / "README.md"
    if not readme.is_file():
        return ["README.md is missing"], ""
    text = readme.read_text(encoding="utf-8")
    for path in ROOT.rglob("._*"):
        errors.append(f"AppleDouble file remains: {path.relative_to(ROOT)}")
    if len(re.findall(r"^#\s+", text, re.M)) != 1:
        errors.append("README.md must have exactly one H1")
    for number, line in enumerate(text.splitlines(), 1):
        prose = LINK.sub(lambda match: match[1], line)
        if CJK.search(URL.sub("", prose)):
            errors.append(f"README.md:{number}: untranslated CJK prose")
        label = LABEL.match(line)
        if label and not label[1].strip("*_` "):
            errors.append(f"README.md:{number}: empty resource label")
    duplicates = [name for name, count in Counter(ANCHOR.findall(text)).items() if count > 1]
    errors.extend(f"README.md: duplicate explicit anchor #{name}" for name in duplicates)

    documents = {path: path.read_text(encoding="utf-8") for path in ROOT.rglob("*.md")
                 if not path.name.startswith("._") and ".git" not in path.parts}
    local_count = 0
    for path, contents in documents.items():
        for match in LINK.finditer(contents):
            destination = match[2].strip("<>")
            parsed = urlsplit(destination)
            if parsed.scheme or parsed.netloc:
                continue
            local_count += 1
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            location = f"{path.relative_to(ROOT)}:{contents.count(chr(10), 0, match.start()) + 1}"
            if not target.exists():
                errors.append(f"{location}: missing local destination {destination}")
            elif parsed.fragment and target.suffix.lower() == ".md":
                target_text = documents.get(target)
                if target_text is None:
                    target_text = target.read_text(encoding="utf-8")
                if unquote(parsed.fragment) not in anchors(target_text):
                    errors.append(f"{location}: missing fragment {destination}")

    comparison = ""
    if upstream:
        source_path = Path(upstream)
        if source_path.is_dir():
            source_path /= "README.md"
        if not source_path.is_file():
            errors.append(f"Upstream README not found: {source_path}")
        else:
            source = source_path.read_text(encoding="utf-8")
            old_urls, old_titles = paper_resources(source), paper_titles(source)
            for url, count in (old_urls - paper_resources(text)).items():
                errors.append(f"README.md: missing {count} source URL occurrence(s): {url}")
            for title, count in (old_titles - paper_titles(text)).items():
                errors.append(f"README.md: missing {count} source title occurrence(s): {title}")
            comparison = f"; {sum(old_urls.values())} source resource URLs and {sum(old_titles.values())} titles compared"
    summary = f"README.md; {len(documents)} Markdown files; {local_count} local links{comparison}"
    return errors, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, help="Upstream README.md or its directory")
    args = parser.parse_args()
    errors, summary = validate(args.upstream)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"{'FAIL' if errors else 'PASS'}: {summary}; {len(errors)} error(s)")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
