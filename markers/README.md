# Verse rendering marker DTOs

Each `<Book>.json` file mirrors the clean book's chapter and verse keys. A
verse entry has this shape:

```json
{
  "paragraph_start": true,
  "added_words": [{"start": 55, "end": 58}],
  "words_of_christ": [{"start": 0, "end": 14}]
}
```

- `paragraph_start` tells a reader to begin a paragraph before the verse.
- `added_words` identifies words shown in brackets by the provider.
- `words_of_christ` identifies red-letter ranges.
- Offsets are zero-based Unicode code-point offsets into the corresponding
  clean verse in `<Book>.json`.
- `start` is inclusive and `end` is exclusive.
- Empty arrays mean that rendering treatment does not occur in the verse.

The sidecars were extracted during the repository's external alignment.
`python script.py audit` validates their structure and span bounds offline;
`python script.py credible-check` temporarily downloads the comparison corpus
and checks every marker entry against it.
