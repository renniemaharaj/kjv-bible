#!/usr/bin/env python3
"""Validate and fingerprint the 66 JSON files in this repository."""

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from typing import Final, NamedTuple, TextIO, TypeAlias, cast


BookData: TypeAlias = dict[str, dict[str, str]]
BookSpec: TypeAlias = tuple[str, int, int]

ROOT: Final[Path] = Path(__file__).resolve().parent
SUMS_FILE: Final[Path] = ROOT / "SHA512SUMS"
README_FILE: Final[Path] = ROOT / "README.md"
METADATA_FILE: Final[Path] = ROOT / "kjv.json"
MARKERS_DIR: Final[Path] = ROOT / "markers"
CREDIBLE_DIR: Final[Path] = ROOT / "credible"
DOWNLOAD_FILE: Final[Path] = CREDIBLE_DIR / "biblesupersearch-kjv.json"
REPORT_FILE: Final[Path] = CREDIBLE_DIR / "inconsistencies.jsonl"
DOWNLOAD_URL: Final[str] = (
    "https://api.biblesupersearch.com/api/download?bible=kjv&format=json"
)
USER_AGENT: Final[str] = "kjv-bible-audit/1.0"
JsonObject: TypeAlias = dict[str, object]
MarkerBooks: TypeAlias = dict[str, JsonObject]
BookCounts: TypeAlias = tuple[int, int]

# Canonical Protestant order. Chapter and verse totals are the traditional KJV
# versification, independently published by the references linked in README.md.
BOOKS: Final[list[BookSpec]] = [
    ("Genesis", 50, 1533), ("Exodus", 40, 1213), ("Leviticus", 27, 859),
    ("Numbers", 36, 1288), ("Deuteronomy", 34, 959), ("Joshua", 24, 658),
    ("Judges", 21, 618), ("Ruth", 4, 85), ("1 Samuel", 31, 810),
    ("2 Samuel", 24, 695), ("1 Kings", 22, 816), ("2 Kings", 25, 719),
    ("1 Chronicles", 29, 942), ("2 Chronicles", 36, 822), ("Ezra", 10, 280),
    ("Nehemiah", 13, 406), ("Esther", 10, 167), ("Job", 42, 1070),
    ("Psalms", 150, 2461), ("Proverbs", 31, 915), ("Ecclesiastes", 12, 222),
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
BOOK_COUNTS: Final[dict[str, BookCounts]] = {
    book: (chapters, verses) for book, chapters, verses in BOOKS
}


class ValidationError(ValueError):
    """Raised when a source file cannot be trusted as structurally valid."""


class ApiError(RuntimeError):
    """Raised when the temporary comparison source is incomplete or invalid."""


class SourceArtifacts(NamedTuple):
    corpus: dict[str, BookData]
    markers: MarkerBooks


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
    actual_files = {
        path.name for path in ROOT.glob("*.json") if path != METADATA_FILE
    }
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


def load_json(path: Path) -> object:
    try:
        with path.open(encoding="utf-8") as source:
            return cast(
                object,
                json.load(source, object_pairs_hook=reject_duplicate_keys),
            )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"{path}: {error}") from error


def require_object(value: object, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValidationError(f"{context} must be a JSON object")
    if not all(isinstance(key, str) for key in value):
        raise ValidationError(f"{context} keys must be strings")
    return cast(dict[str, object], value)


def validate_metadata() -> None:
    metadata = require_object(load_json(METADATA_FILE), str(METADATA_FILE))
    required = {
        "schema_version",
        "name",
        "abbreviation",
        "language",
        "translation_history",
        "repository_provenance",
        "text_format",
    }
    if set(metadata) != required or metadata["schema_version"] != 1:
        raise ValidationError(f"{METADATA_FILE} has an invalid schema")
    provenance = require_object(
        metadata["repository_provenance"], "kjv.json repository_provenance"
    )
    verification = require_object(
        provenance.get("verification"), "kjv.json verification"
    )
    if verification.get("verse_count") != 31102:
        raise ValidationError("kjv.json verification verse_count must be 31102")
    text_format = require_object(metadata["text_format"], "kjv.json text_format")
    if text_format.get("rendering_markers") != "markers/<Book>.json":
        raise ValidationError("kjv.json must reference markers/<Book>.json")


def validate_span_list(value: object, text: str, context: str) -> None:
    if not isinstance(value, list):
        raise ValidationError(f"{context} must be an array")
    previous_end = -1
    for number, raw_span in enumerate(value, start=1):
        span = require_object(raw_span, f"{context} span {number}")
        if set(span) != {"start", "end"}:
            raise ValidationError(f"{context} span {number} has invalid fields")
        start = span["start"]
        end = span["end"]
        if (
            not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
            or start < 0
            or start >= end
            or end > len(text)
            or start < previous_end
        ):
            raise ValidationError(f"{context} span {number} is invalid")
        previous_end = end


def validate_markers(validated: Mapping[str, BookData]) -> None:
    expected_files = {f"{book}.json" for book, _, _ in BOOKS}
    actual_files = {path.name for path in MARKERS_DIR.glob("*.json")}
    if actual_files != expected_files:
        raise ValidationError("markers must contain exactly 66 canonical book files")

    for book, data in validated.items():
        marker = require_object(
            load_json(MARKERS_DIR / f"{book}.json"), f"markers/{book}.json"
        )
        if (
            marker.get("schema_version") != 1
            or marker.get("book") != book
            or marker.get("offset_unit") != "Unicode code points"
            or marker.get("span_end") != "exclusive"
        ):
            raise ValidationError(f"markers/{book}.json has invalid metadata")
        chapters = require_object(
            marker.get("chapters"), f"markers/{book}.json chapters"
        )
        if list(chapters) != list(data):
            raise ValidationError(f"markers/{book}.json chapter keys do not align")
        for chapter, verses in data.items():
            marker_verses = require_object(
                chapters[chapter], f"markers/{book}.json chapter {chapter}"
            )
            if list(marker_verses) != list(verses):
                raise ValidationError(
                    f"markers/{book}.json chapter {chapter} verses do not align"
                )
            for verse, text in verses.items():
                context = f"markers/{book}.json {chapter}:{verse}"
                entry = require_object(marker_verses[verse], context)
                if set(entry) != {
                    "paragraph_start",
                    "added_words",
                    "words_of_christ",
                } or not isinstance(entry["paragraph_start"], bool):
                    raise ValidationError(f"{context} has invalid fields")
                validate_span_list(entry["added_words"], text, f"{context} added_words")
                validate_span_list(
                    entry["words_of_christ"], text, f"{context} words_of_christ"
                )


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


def download_comparison_source(timeout: float) -> bytes:
    request = urllib.request.Request(
        DOWNLOAD_URL,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return cast(bytes, response.read())
    except (OSError, urllib.error.URLError) as error:
        raise ApiError(f"Bible download failed: {error}") from error


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        temporary_path.replace(path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def marked_verse(text: str) -> tuple[str, JsonObject]:
    plain: list[str] = []
    paragraph_start = False
    added_start: int | None = None
    red_start: int | None = None
    added_words: list[JsonObject] = []
    words_of_christ: list[JsonObject] = []

    for character in text:
        offset = len(plain)
        if character == "¶":
            if paragraph_start:
                raise ApiError("verse contains more than one paragraph marker")
            paragraph_start = True
        elif character == "[":
            if added_start is not None:
                raise ApiError("verse contains nested added-word markers")
            added_start = offset
        elif character == "]":
            if added_start is None:
                raise ApiError("verse contains an unmatched added-word close marker")
            added_words.append({"start": added_start, "end": offset})
            added_start = None
        elif character == "‹":
            if red_start is not None:
                raise ApiError("verse contains nested red-letter markers")
            red_start = offset
        elif character == "›":
            if red_start is None:
                raise ApiError("verse contains an unmatched red-letter close marker")
            words_of_christ.append({"start": red_start, "end": offset})
            red_start = None
        else:
            plain.append(character)

    if added_start is not None or red_start is not None:
        raise ApiError("verse contains an unclosed rendering marker")
    untrimmed = "".join(plain)
    clean = untrimmed.strip()
    leading = len(untrimmed) - len(untrimmed.lstrip())
    clean_end = leading + len(clean)
    for spans in (added_words, words_of_christ):
        for span in spans:
            start = cast(int, span["start"])
            end = cast(int, span["end"])
            if start < leading or end > clean_end or start >= end:
                raise ApiError("rendering span falls outside verse text")
            span["start"] = start - leading
            span["end"] = end - leading
    return clean, {
        "paragraph_start": paragraph_start,
        "added_words": added_words,
        "words_of_christ": words_of_christ,
    }


def extract_comparison_artifacts(
    payload: object, book_counts: Mapping[str, BookCounts] = BOOK_COUNTS
) -> SourceArtifacts:
    root = require_object(payload, "download")
    metadata = require_object(root.get("metadata"), "download metadata")
    if metadata.get("module") != "kjv":
        raise ApiError(f"download module is not 'kjv': {metadata.get('module')!r}")
    raw_verses = root.get("verses")
    if not isinstance(raw_verses, list) or not raw_verses:
        raise ApiError("download contains no verses")

    corpus: dict[str, BookData] = {}
    markers: MarkerBooks = {}
    for index, raw_entry in enumerate(raw_verses, start=1):
        entry = require_object(raw_entry, f"download verse {index}")
        book = entry.get("book_name")
        chapter = entry.get("chapter")
        verse = entry.get("verse")
        text = entry.get("text")
        if not isinstance(book, str) or book not in book_counts:
            raise ApiError(f"download verse {index}: unknown book {book!r}")
        if not isinstance(chapter, int) or not isinstance(verse, int):
            raise ApiError(f"download verse {index}: invalid reference")
        if not isinstance(text, str) or not text.strip():
            raise ApiError(f"download verse {index}: missing text")
        chapter_key = str(chapter)
        verse_key = str(verse)
        clean, verse_markers = marked_verse(text)
        chapter_data = corpus.setdefault(book, {}).setdefault(chapter_key, {})
        if verse_key in chapter_data:
            raise ApiError(f"duplicate download verse: {book} {chapter}:{verse}")
        chapter_data[verse_key] = clean
        marker_book = markers.setdefault(
            book,
            {
                "schema_version": 1,
                "book": book,
                "offset_unit": "Unicode code points",
                "span_end": "exclusive",
                "chapters": {},
            },
        )
        marker_chapters = cast(dict[str, object], marker_book["chapters"])
        marker_chapter = cast(
            dict[str, object], marker_chapters.setdefault(chapter_key, {})
        )
        marker_chapter[verse_key] = verse_markers

    if set(corpus) != set(book_counts):
        raise ApiError("download does not contain exactly 66 canonical books")
    for book, data in corpus.items():
        expected_chapters, expected_verses = book_counts[book]
        if list(data) != expected_numeric_keys(expected_chapters):
            raise ApiError(f"{book}: incomplete download chapters")
        verse_total = 0
        for chapter, verses in data.items():
            if list(verses) != expected_numeric_keys(len(verses)):
                raise ApiError(f"{book} {chapter}: incomplete download verses")
            verse_total += len(verses)
        if verse_total != expected_verses:
            raise ApiError(
                f"{book}: expected {expected_verses} verses, found {verse_total}"
            )
    return SourceArtifacts(corpus, markers)


def decode_comparison_source(raw_source: bytes) -> object:
    try:
        return cast(object, json.loads(raw_source.decode("utf-8")))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ApiError(f"download is not valid UTF-8 JSON: {error}") from error


def discrepancy_records(
    book: str, local: BookData, provider: BookData
) -> list[JsonObject]:
    records: list[JsonObject] = []
    for chapter, verses in local.items():
        for verse, local_text in verses.items():
            provider_text = provider[chapter][verse]
            if local_text != provider_text:
                records.append(
                    {
                        "reference": f"{book} {chapter}:{verse}",
                        "local": local_text,
                        "provider": provider_text,
                    }
                )
    return records


def write_json_lines(records: list[JsonObject], output: TextIO) -> None:
    for record in records:
        output.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        output.write("\n")


def cleanup_credible() -> None:
    DOWNLOAD_FILE.unlink(missing_ok=True)
    REPORT_FILE.unlink(missing_ok=True)
    CREDIBLE_DIR.rmdir()


def credible_check(validated: Mapping[str, BookData], timeout: float) -> int:
    if timeout <= 0:
        raise ValidationError("--timeout must be positive")
    raw_source = download_comparison_source(timeout)
    atomic_write_bytes(DOWNLOAD_FILE, raw_source)
    artifacts = extract_comparison_artifacts(decode_comparison_source(raw_source))

    records: list[JsonObject] = []
    for book, data in validated.items():
        records.extend(discrepancy_records(book, data, artifacts.corpus[book]))
        committed_markers = load_json(MARKERS_DIR / f"{book}.json")
        if committed_markers != artifacts.markers[book]:
            raise ValidationError(
                f"markers/{book}.json differs from the comparison provider"
            )

    with REPORT_FILE.open("w", encoding="utf-8", newline="\n") as output:
        write_json_lines(records, output)
    if records:
        print(
            f"Found {len(records)} inconsistencies; temporary evidence retained "
            f"in {CREDIBLE_DIR}."
        )
        return 1
    cleanup_credible()
    print(
        "OK: all 31,102 verses and 66 marker sidecars match the provider; "
        "temporary comparison data removed."
    )
    return 0


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
        choices=["audit", "check", "count", "credible-check", "hash", "manifest"],
        help=(
            "audit: validate structure/counts and tracked hashes; "
            "check: validate and scan for embedded verse labels; "
            "count: validate and print counts; hash: print exact-file hashes; "
            "manifest: validate and update SHA512SUMS; credible-check: "
            "temporarily download and compare the complete provider corpus"
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="credible-check download timeout in seconds",
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
        elif args.command == "credible-check":
            validate_metadata()
            validate_markers(validated)
            return credible_check(validated, cast(float, args.timeout))
        elif args.command == "audit":
            verify_manifest()
            verify_readme_fingerprint()
            validate_metadata()
            validate_markers(validated)
            issues = suspicious_labels(validated)
            if issues:
                raise ValidationError(
                    "possible embedded verse labels:\n" + "\n".join(issues)
                )
            print("OK: 66 books, 1,189 chapters, and 31,102 verses validated.")
            print("OK: chapter/verse keys are unique, numeric, and consecutive.")
            print("OK: SHA512SUMS matches every exact JSON file.")
            print("OK: kjv.json metadata and 66 marker sidecars validated.")
            print(f"Corpus SHA-512: {corpus_fingerprint()}")
    except (ApiError, ValidationError, OSError, UnicodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
