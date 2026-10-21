# Test Data

[English](README.md) | [Polski](README.pl.md)

| File | Purpose | Expected behavior |
|---|---|---|
| `sample.csv` | CSV with Polish characters, an empty field, a comma, quotes, and a multiline value | CSV → JSON: 5 objects, headers in source order, the empty value remains `""`, Unicode is preserved |
| `sample.json` | Array of objects with a nested object, a missing key, and boolean values | JSON → CSV: headers `imię, nazwisko, miasto, uwagi, aktywny, adres`; missing key → empty cell; nested object → JSON string |
| `sample.txt` | Text file with Polish and Cyrillic characters and blank lines | TXT → DOCX/PDF: every paragraph is preserved, Unicode is not lost |
| `sample.docx` | DOCX with a heading, paragraphs, Unicode, and a table | DOCX → TXT/PDF/ODT: text and table are preserved; PDF is created through LibreOffice |
| `sample.odt` | ODT with paragraphs, Unicode, and a table | ODT → TXT/PDF/DOCX: text and table are preserved; PDF and DOCX are created through LibreOffice |

The files are used for manual checks. Automated tests additionally create their own temporary files, including malformed documents and edge cases.
