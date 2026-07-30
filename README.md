# KJV Bible JSON Repository

This repository contains the 66 books of the King James Version (KJV) Bible as
chapter-and-verse JSON objects. It is intended to be a transparent,
machine-readable source whose exact contents can be audited and fingerprinted.

## Repository contents

- `*.json` — one UTF-8 JSON file per Bible book
- `SHA512SUMS` — SHA-512 digest of every exact JSON file
- `script.py` — structural, count, and integrity checks
- `names.py` / `names.ts` — TypeScript filename-list generator and output

## Verify the corpus

Run the complete audit:

```bash
python script.py audit
```

The audit fails if:

- any of the 66 expected books is missing or an unexpected JSON file is present;
- JSON is invalid or contains duplicate keys;
- chapter or verse keys are missing, repeated, non-consecutive, or out of order;
- a verse is empty or is not a string;
- a book's chapter or verse total differs from the published KJV counts; or
- an exact-file SHA-512 digest differs from the tracked `SHA512SUMS` manifest.

The manifest can also be checked without Python:

```bash
sha512sum -c SHA512SUMS
```

After intentionally reviewing changes to the Bible JSON, regenerate the
manifest and README corpus fingerprint with:

```bash
python script.py manifest
```

Do not regenerate the manifest merely to silence an audit failure: inspect the
changed verses first.

## Commit quality gate

Install the development checker and enable the tracked Git hook once per clone:

```bash
python -m pip install -r requirements-dev.txt
git config core.hooksPath .githooks
```

Before every commit, `.githooks/pre-commit` exports the Git index to an isolated
temporary directory and checks that exact staged snapshot. It runs strict
`mypy` checking on both Python files, followed by the complete corpus audit.
The commit fails if typing, JSON structure, any per-book count, the
`SHA512SUMS` manifest, or the README corpus fingerprint is invalid or stale.
This staged-snapshot approach also catches partially staged corpus updates.

Run the same gates manually against the working tree with:

```bash
python -m mypy
python script.py audit
```

## Last verified result

Audit run: **2026-07-30**

| Scope | Books | Chapters | Verses |
| --- | ---: | ---: | ---: |
| Old Testament | 39 | 929 | 23,145 |
| New Testament | 27 | 260 | 7,957 |
| **Complete KJV** | **66** | **1,189** | **31,102** |

<details>
<summary>Per-book verified counts</summary>

| Book | Chapters | Verses |
| --- | ---: | ---: |
| Genesis | 50 | 1,533 |
| Exodus | 40 | 1,213 |
| Leviticus | 27 | 859 |
| Numbers | 36 | 1,288 |
| Deuteronomy | 34 | 959 |
| Joshua | 24 | 658 |
| Judges | 21 | 618 |
| Ruth | 4 | 85 |
| 1 Samuel | 31 | 810 |
| 2 Samuel | 24 | 695 |
| 1 Kings | 22 | 816 |
| 2 Kings | 25 | 719 |
| 1 Chronicles | 29 | 942 |
| 2 Chronicles | 36 | 822 |
| Ezra | 10 | 280 |
| Nehemiah | 13 | 406 |
| Esther | 10 | 167 |
| Job | 42 | 1,070 |
| Psalms | 150 | 2,461 |
| Proverbs | 31 | 915 |
| Ecclesiastes | 12 | 222 |
| Song of Solomon | 8 | 117 |
| Isaiah | 66 | 1,292 |
| Jeremiah | 52 | 1,364 |
| Lamentations | 5 | 154 |
| Ezekiel | 48 | 1,273 |
| Daniel | 12 | 357 |
| Hosea | 14 | 197 |
| Joel | 3 | 73 |
| Amos | 9 | 146 |
| Obadiah | 1 | 21 |
| Jonah | 4 | 48 |
| Micah | 7 | 105 |
| Nahum | 3 | 47 |
| Habakkuk | 3 | 56 |
| Zephaniah | 3 | 53 |
| Haggai | 2 | 38 |
| Zechariah | 14 | 211 |
| Malachi | 4 | 55 |
| Matthew | 28 | 1,071 |
| Mark | 16 | 678 |
| Luke | 24 | 1,151 |
| John | 21 | 879 |
| Acts | 28 | 1,007 |
| Romans | 16 | 433 |
| 1 Corinthians | 16 | 437 |
| 2 Corinthians | 13 | 257 |
| Galatians | 6 | 149 |
| Ephesians | 6 | 155 |
| Philippians | 4 | 104 |
| Colossians | 4 | 95 |
| 1 Thessalonians | 5 | 89 |
| 2 Thessalonians | 3 | 47 |
| 1 Timothy | 6 | 113 |
| 2 Timothy | 4 | 83 |
| Titus | 3 | 46 |
| Philemon | 1 | 25 |
| Hebrews | 13 | 303 |
| James | 5 | 108 |
| 1 Peter | 5 | 105 |
| 2 Peter | 3 | 61 |
| 1 John | 5 | 105 |
| 2 John | 1 | 13 |
| 3 John | 1 | 14 |
| Jude | 1 | 25 |
| Revelation | 22 | 404 |

</details>

Every per-book result produced by `python script.py count` matches the KJV
tables published by
[Bible SuperSearch](https://www.biblesupersearch.com/2019/02/the-number-of-verses-in-the-bible/)
and
[Grace Ambassadors](https://graceambassadors.com/bible/king-james-bible-statistics).

Exact corpus SHA-512:

```text
f49b390066c3113fbb708b96406acc6a02dffe9c56835154d73b6caa45123ede112544ede09e0ed8db43c1d7481feed46a1a2bb212d8261b25b9aaa6d7a3a8b2
```

The corpus fingerprint is deterministic and covers each canonical filename and
every byte of its file, in biblical order. `script.py` begins with the
domain-separation bytes `KJV-JSON-CORPUS\0v1\0`, then hashes, for each book:
a 4-byte big-endian filename length, its UTF-8 filename, an 8-byte big-endian
file length, and the raw file bytes. Length framing prevents ambiguous
concatenations, and the fixed book order makes the result independent of
filesystem traversal order.

The per-file values in [`SHA512SUMS`](SHA512SUMS) are plain SHA-512 hashes of
the raw files. Together, these fingerprints prove that a copy is byte-for-byte
identical to this tracked snapshot. A hash does **not** by itself prove that
the underlying wording is correct or establish which historical KJV edition
supplied it.

## Text provenance

The repository history identifies this corpus as the KJV, but does not
currently document the upstream transcription or exact KJV edition. That
source lineage should be recorded here when it is established. Until then, the
checks provide strong structural and change integrity, while the claim of
textual provenance remains limited to the repository's review history.

## Utility commands

```bash
python script.py count     # validated chapter and verse totals by book
python script.py check     # structure plus scan for embedded verse labels
python script.py hash      # exact-file hashes plus the corpus fingerprint
python script.py audit     # all validation and tracked-manifest verification
python script.py manifest  # intentionally update hashes in SHA512SUMS/README
```

To regenerate the TypeScript list of the 66 JSON filenames:

```bash
python names.py
```

## Contributing

Corrections are welcome through pull requests. For any Bible-text change,
please identify the verse, cite the KJV edition or source used, explain the
change, run `python script.py manifest`, and commit the resulting
`SHA512SUMS` update with the JSON change.

## License

This repository is available under the MIT License.

## Acknowledgments

The King James Version text is in the public domain in many jurisdictions.
