#!/usr/bin/env python3
"""Validate and fingerprint the 66 JSON files in this repository."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Final, TypeAlias, cast


BookData: TypeAlias = dict[str, dict[str, str]]
BookSpec: TypeAlias = tuple[str, int, int]

ROOT: Final[Path] = Path(__file__).resolve().parent
SUMS_FILE: Final[Path] = ROOT / "SHA512SUMS"
README_FILE: Final[Path] = ROOT / "README.md"

# Canonical Protestant order. Chapter and verse totals are the traditional KJV
# versification, independently published by the references linked in README.md.
BOOKS: Final[list[BookSpec]] = [
    ("Genesis", 50, 1533), ("Exodus", 40, 1213), ("Leviticus", 27, 859),
    ("Numbers", 36, 1288), ("Deuteronomy", 34, 959), ("Joshua", 24, 658),
    ("Judges", 21, 618), ("Ruth", 4, 85), ("1 Samuel", 31, 810),
    ("2 Samuel", 24, 695), ("1 Kings", 22, 816), ("2 Kings", 25, 719),
    ("1 Chronicles", 29, 942), ("2 Chronicles", 36, 822), ("Ezra", 10, 280),
    ("Nehemiah", 13, 406), ("Esther", 10, 167), ("Job", 42, 1070),
    ("Psalm", 150, 2461), ("Proverbs", 31, 915), ("Ecclesiastes", 12, 222),
    ("Song of Solomon", 8, 117), ("Isaiah", 66, 1292),
    ("Jeremiah", 52, 1364), ("Lamentations", 5, 154),
    ("Ezekiel", 48, 1273), ("Daniel", 12, 357), ("Hosea", 14, 197),
    ("Joel", 3, 73), ("Amos", 9, 146), ("Obadiah", 1, 21),
    ("Jonah", 4, 48), ("Micah", 7, 105), ("Nahum", 3, 47),
    ("Habakkuk", 3, 56), ("Zephaniah", 3, 53), ("Haggai", 2, 38),
    ("Zechariah", 14, 211), ("Malachi", 4, 55), ("Matthew", 28, 1071),
    ("Mark", 16, 678), ("Luke", 24, 1151), ("John", 21, 879),
    ("Acts", 28, 1007), ("Romans", 16, 433), ("1 Corinthians", 16, 437),
    ("2 Corinthians", 13, 257), ("Galatians", 6, 149),
    ("Ephesians", 6, 155), ("Philippians", 4, 104),
    ("Colossians", 4, 95), ("1 Thessalonians", 5, 89),
    ("2 Thessalonians", 3, 47), ("1 Timothy", 6, 113),
    ("2 Timothy", 4, 83), ("Titus", 3, 46), ("Philemon", 1, 25),
    ("Hebrews", 13, 303), ("James", 5, 108), ("1 Peter", 5, 105),
    ("2 Peter", 3, 61), ("1 John", 5, 105), ("2 John", 1, 13),
    ("3 John", 1, 14), ("Jude", 1, 25), ("Revelation", 22, 404),
]


class ValidationError(ValueError):
    """Raised when a source file cannot be trusted as structurally valid."""


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Prevent json.load from silently overwriting duplicate chapter/verse keys."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def expected_numeric_keys(count: int) -> list[str]:
    return [str(number) for number in range(1, count + 1)]


def validate_book(
    path: Path, expected_chapters: int, expected_verses: int
) -> BookData:
    try:
        with path.open(encoding="utf-8") as source:
            raw_data: object = json.load(
                source, object_pairs_hook=reject_duplicate_keys
            )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(str(error)) from error

    if not isinstance(raw_data, dict):
        raise ValidationError("top-level JSON value must be an object")

    data = cast(dict[object, object], raw_data)
    chapter_keys = list(data)
    expected_chapters_keys = expected_numeric_keys(expected_chapters)
    if chapter_keys != expected_chapters_keys:
        raise ValidationError(
            f"chapters must be exactly 1..{expected_chapters} in numeric order"
        )

    verse_total = 0
    validated: BookData = {}
    for raw_chapter, raw_verses in data.items():
        if not isinstance(raw_chapter, str):
            raise ValidationError("chapter keys must be strings")
        chapter = raw_chapter
        if not isinstance(raw_verses, dict) or not raw_verses:
            raise ValidationError(f"chapter {chapter} must be a non-empty object")
        verses = cast(dict[object, object], raw_verses)
        expected_verses_keys = expected_numeric_keys(len(verses))
        if list(verses) != expected_verses_keys:
            raise ValidationError(
                f"chapter {chapter} verses must be consecutive from 1"
            )
        validated_verses: dict[str, str] = {}
        for raw_verse, raw_text in verses.items():
            if not isinstance(raw_verse, str):
                raise ValidationError(
                    f"chapter {chapter} verse keys must be strings"
                )
            verse = raw_verse
            if not isinstance(raw_text, str) or not raw_text.strip():
                raise ValidationError(
                    f"chapter {chapter}, verse {verse} must contain text"
                )
            validated_verses[verse] = raw_text
        validated[chapter] = validated_verses
        verse_total += len(verses)

    if verse_total != expected_verses:
        raise ValidationError(
            f"expected {expected_verses} verses, found {verse_total}"
        )
    return validated


def validate_corpus() -> dict[str, BookData]:
    expected_files = {f"{book}.json" for book, _, _ in BOOKS}
    actual_files = {path.name for path in ROOT.glob("*.json")}
    missing = sorted(expected_files - actual_files)
    unexpected = sorted(actual_files - expected_files)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected: {', '.join(unexpected)}")
        raise ValidationError("; ".join(details))

    validated: dict[str, BookData] = {}
    for book, chapters, verses in BOOKS:
        path = ROOT / f"{book}.json"
        validated[book] = validate_book(path, chapters, verses)
    return validated


def sha512_file(path: Path) -> str:
    digest = hashlib.sha512()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def book_hashes() -> list[tuple[str, str]]:
    return [
        (f"{book}.json", sha512_file(ROOT / f"{book}.json"))
        for book, _, _ in BOOKS
    ]


def corpus_fingerprint() -> str:
    """Hash exact source bytes with unambiguous length-delimited framing."""
    digest = hashlib.sha512(b"KJV-JSON-CORPUS\x00v1\x00")
    for book, _, _ in BOOKS:
        filename = f"{book}.json".encode("utf-8")
        content = (ROOT / f"{book}.json").read_bytes()
        digest.update(len(filename).to_bytes(4, "big"))
        digest.update(filename)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def manifest_text() -> str:
    return "".join(f"{digest}  {filename}\n" for filename, digest in book_hashes())


def verify_manifest() -> None:
    if not SUMS_FILE.exists():
        raise ValidationError("SHA512SUMS is missing; run: python script.py manifest")
    expected = manifest_text()
    actual = SUMS_FILE.read_text(encoding="utf-8")
    if actual != expected:
        raise ValidationError(
            "SHA512SUMS does not match the source files; review changes, then run: "
            "python script.py manifest"
        )


def update_readme_fingerprint() -> None:
    fingerprint = corpus_fingerprint()
    readme = README_FILE.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(Exact corpus SHA-512:\n\n```text\n)[0-9a-f]{128}(\n```)"
    )
    updated, replacements = pattern.subn(rf"\g<1>{fingerprint}\g<2>", readme)
    if replacements != 1:
        raise ValidationError(
            "README must contain exactly one formatted corpus SHA-512 block"
        )
    README_FILE.write_text(updated, encoding="utf-8")


def verify_readme_fingerprint() -> None:
    fingerprint = corpus_fingerprint()
    readme = README_FILE.read_text(encoding="utf-8")
    if f"Exact corpus SHA-512:\n\n```text\n{fingerprint}\n```" not in readme:
        raise ValidationError(
            "README corpus fingerprint is stale; run: python script.py manifest"
        )


def suspicious_labels(validated: dict[str, BookData]) -> list[str]:
    issues: list[str] = []
    for book, data in validated.items():
        label = re.compile(rf"^(?:[1-3]\s*)?{re.escape(book)}\s+\d+:\d+\b", re.I)
        for chapter, verses in data.items():
            for verse, text in verses.items():
                if label.match(text):
                    issues.append(f"{book} {chapter}:{verse}: {text}")
    return issues


def print_counts() -> None:
    for book, chapters, verses in BOOKS:
        chapter_label = "chapter" if chapters == 1 else "chapters"
        print(f"{book}: {chapters} {chapter_label}, {verses} verses")
    print("\nBooks: 66")
    print("Chapters: 1,189")
    print("Verses: 31,102")


def print_hashes() -> None:
    for filename, digest in book_hashes():
        print(f"{digest}  {filename}")
    print(f"\nCorpus SHA-512: {corpus_fingerprint()}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and fingerprint the repository's KJV JSON corpus"
    )
    parser.add_argument(
        "command",
        choices=["audit", "check", "count", "hash", "manifest"],
        help=(
            "audit: validate structure/counts and tracked hashes; "
            "check: validate and scan for embedded verse labels; "
            "count: validate and print counts; hash: print exact-file hashes; "
            "manifest: validate and update SHA512SUMS"
        ),
    )
    args = parser.parse_args()

    try:
        validated = validate_corpus()
        if args.command == "count":
            print_counts()
        elif args.command == "hash":
            print_hashes()
        elif args.command == "check":
            issues = suspicious_labels(validated)
            if issues:
                raise ValidationError(
                    "possible embedded verse labels:\n" + "\n".join(issues)
                )
            print("OK: 66 books passed structural and embedded-label checks.")
        elif args.command == "manifest":
            issues = suspicious_labels(validated)
            if issues:
                raise ValidationError(
                    "possible embedded verse labels:\n" + "\n".join(issues)
                )
            SUMS_FILE.write_text(manifest_text(), encoding="utf-8")
            update_readme_fingerprint()
            print(f"Updated {SUMS_FILE.name}")
            print(f"Updated {README_FILE.name} corpus fingerprint")
            print(f"Corpus SHA-512: {corpus_fingerprint()}")
        elif args.command == "audit":
            verify_manifest()
            verify_readme_fingerprint()
            issues = suspicious_labels(validated)
            if issues:
                raise ValidationError(
                    "possible embedded verse labels:\n" + "\n".join(issues)
                )
            print("OK: 66 books, 1,189 chapters, and 31,102 verses validated.")
            print("OK: chapter/verse keys are unique, numeric, and consecutive.")
            print("OK: SHA512SUMS matches every exact JSON file.")
            print(f"Corpus SHA-512: {corpus_fingerprint()}")
    except (ValidationError, OSError, UnicodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
