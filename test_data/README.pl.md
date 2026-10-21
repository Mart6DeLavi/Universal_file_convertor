# Dane testowe

[English](README.md) | [Polski](README.pl.md)

| Plik | Przeznaczenie | Oczekiwane zachowanie |
|---|---|---|
| `sample.csv` | CSV z polskimi znakami, pustym polem, przecinkiem, cudzysłowami i wartością wielowierszową | CSV → JSON: 5 obiektów, nagłówki w kolejności źródłowej, pusta wartość pozostaje `""`, Unicode jest zachowany |
| `sample.json` | Tablica obiektów z zagnieżdżonym obiektem, brakującym kluczem i wartościami logicznymi | JSON → CSV: nagłówki `imię, nazwisko, miasto, uwagi, aktywny, adres`; brakujący klucz → pusta komórka; zagnieżdżony obiekt → ciąg JSON |
| `sample.txt` | Plik tekstowy z polskimi i cyrylickimi znakami oraz pustymi wierszami | TXT → DOCX/PDF: każdy akapit jest zachowany, Unicode nie ginie |
| `sample.docx` | DOCX z nagłówkiem, akapitami, Unicode i tabelą | DOCX → TXT/PDF/ODT: tekst i tabela są zachowane; PDF jest tworzony przez LibreOffice |
| `sample.odt` | ODT z akapitami, Unicode i tabelą | ODT → TXT/PDF/DOCX: tekst i tabela są zachowane; PDF i DOCX są tworzone przez LibreOffice |

Pliki służą do kontroli ręcznej. Testy automatyczne dodatkowo tworzą własne pliki tymczasowe, w tym uszkodzone dokumenty i przypadki graniczne.
