# Raport z testów

[English](test_report.md) | [Polski](test_report.pl.md)

Data testów: 21 października 2026.

## Środowisko

| Komponent | Wersja |
|---|---|
| System | macOS 26.6.2 (build 25G83) |
| Python | 3.14.8 |
| Tk / Tcl | 9.1 / 9.1 |
| pytest | 9.1.1 |
| CustomTkinter | 6.0.0 |
| python-docx | 1.2.0 |
| ReportLab | 5.0.1 |
| pypdf | 6.21.1 |
| Pillow | 13.0.0 |
| LibreOffice | 26.8.1.1 |

LibreOffice został zainstalowany przez Homebrew i jest wykrywany przez aplikację jako `/opt/homebrew/bin/soffice`. Standardowa ścieżka aplikacji `/Applications/LibreOffice.app/Contents/MacOS/soffice` również jest rozpoznawana.

## Polecenie testowe

```bash
.venv/bin/python -m pytest -v
```

## Wynik

```text
60 passed in 5.62s
```

Nie ma błędów ani pominiętych testów. Wszystkie dziesięć kierunków z matrycy zadania jest zaimplementowanych i zweryfikowanych w tym środowisku.

## Testy automatyczne według modułów

| Plik | Testy | Co jest sprawdzane |
|---|---:|---|
| `tests/test_csv_json.py` | 14 | CSV ↔ JSON, Unicode, BOM, cudzysłowy, przecinki, pola wielowierszowe, puste wartości, separatory, błędy nagłówków i struktury, pusta tablica, roundtrip |
| `tests/test_document_converters.py` | 8 | Rzeczywiste konwersje biurowe przez LibreOffice, brak zależności, limit czasu, niezerowy kod wyjścia, brak wyniku, zachowanie źródła |
| `tests/test_registry.py` | 6 | Rejestr, zestaw kierunków, filtrowanie celów zależnych od LibreOffice, duplikaty, delegowanie do serwisu |
| `tests/test_service.py` | 8 | Pełny przepływ serwisu, konflikty, nadpisanie, unikalne nazwy, foldery tymczasowe, pusty CSV, zachowanie źródła przy błędzie |
| `tests/test_text_converters.py` | 6 | TXT ↔ DOCX, TXT → PDF, ODT → TXT, Unicode, tabele, uszkodzone dokumenty |
| `tests/test_validators.py` | 12 | Walidacja źródła, rozszerzeń, formatu docelowego, katalogu, nazwy, konfliktów i zależności LibreOffice |

## Weryfikacja kierunków biurowych

Każdy test używa dokumentu z tekstem Unicode i spacjami w nazwie pliku. Po konwersji sprawdzane jest zarówno istnienie pliku, jak i jego zawartość.

| Kierunek | Sprawdzenie wyniku | Status |
|---|---|---|
| DOCX → PDF | Sygnatura `%PDF`, ekstrakcja tekstu przez `pypdf`, obecność `Zażółć` i `Łódź` | Zaliczony |
| ODT → PDF | Sygnatura `%PDF`, ekstrakcja tekstu przez `pypdf`, obecność tekstu Unicode | Zaliczony |
| DOCX → ODT | Otwarcie przez `odfpy`, ekstrakcja tekstu, obecność tekstu Unicode | Zaliczony |
| ODT → DOCX | Otwarcie przez `python-docx`, obecność tekstu Unicode | Zaliczony |

Dodatkowo każdy test porównuje bajty pliku źródłowego przed i po konwersji. Dokumenty źródłowe nie są zmieniane.

## Weryfikacja end-to-end wszystkich 10 kierunków

Wszystkie kierunki wykonano także przez publiczne API `ConversionService.execute` na plikach z `test_data/`. Każdy wynik otwarto odpowiednim parserem: `json`, `csv`, `python-docx`, `odfpy` lub `pypdf`.

| # | Kierunek | Sprawdzenie wyniku | Rozmiar |
|---:|---|---|---:|
| 1 | CSV → JSON | Tablica JSON odczytana poprawnie | 591 bajtów |
| 2 | JSON → CSV | CSV odczytany poprawnie | 167 bajtów |
| 3 | TXT → DOCX | DOCX otwarty, tekst obecny | 36 845 bajtów |
| 4 | DOCX → TXT | Tekst wyodrębniony | 230 bajtów |
| 5 | TXT → PDF | PDF otwarty, tekst wyodrębniony | 36 939 bajtów |
| 6 | DOCX → PDF | PDF otwarty, tekst wyodrębniony | 29 331 bajtów |
| 7 | ODT → PDF | PDF otwarty, tekst wyodrębniony | 21 259 bajtów |
| 8 | DOCX → ODT | ODT otwarty przez `odfpy` | 14 964 bajty |
| 9 | ODT → DOCX | DOCX otwarty, tekst obecny | 5 119 bajtów |
| 10 | ODT → TXT | Tekst wyodrębniony | 230 bajtów |

Wszystkie dziesięć kontroli zakończyło się pomyślnie. Pliki źródłowe nie zostały zmienione.

## Weryfikacja GUI

Przeprojektowane okno CustomTkinter sprawdzono z rzeczywistym `MainWindow`, wątkiem konwersji w tle i osobnym pustym folderem docelowym dla każdego przypadku.

### Układ

| Kontrola | Wynik |
|---|---|
| Domyślny rozmiar okna | `1180x720` |
| Minimalny rozmiar okna | `1000x620` |
| Przewijane kontenery | Brak; brak `CTkScrollableFrame` |
| Widoczne paski przewijania | Brak przy domyślnym i minimalnym rozmiarze |
| Wszystkie kontrolki źródła widoczne przy minimalnym rozmiarze | Tak |
| Postęp i status widoczne przy minimalnym rozmiarze | Tak |
| Panel wyniku zaczyna w stanie pustym | Tak |
| Stan sukcesu pokazuje nazwę, ścieżkę, format, rozmiar, czas i przyciski otwierania | Tak |
| Długie ścieżki zawijają się bez przycinania kontrolek | Tak |
| Język interfejsu | Angielski i polski, przełączany w nagłówku; wybór zapamiętywany |
| Pasek postępu | Deterministyczny, z procentami; brak animacji tam i z powrotem |
| Stan konwersji | Wyśrodkowany stan w prawym panelu; tekst nie przesuwa się poziomo |
| Przełącznik motywu | Działa |

### Konwersje przez GUI

| Plik źródłowy | Cel | Dostępne cele | Wynik |
|---|---|---|---|
| `test_data/sample.csv` | JSON | JSON | Plik utworzony; karta wyniku zaktualizowana |
| `test_data/sample.txt` | PDF | DOCX, PDF | Plik utworzony; PDF otwarty i tekst wyodrębniony |
| `test_data/sample.docx` | PDF | TXT, ODT, PDF | Plik utworzony; PDF zawiera tekst Unicode |
| `test_data/sample.odt` | DOCX | TXT, DOCX, PDF | Plik utworzony; tekst czytelny przez `python-docx` |

Interfejs się nie zawieszał, zdarzenia postępu trafiały z serwisu do GUI przez kolejkę, status zakończenia był aktualizowany po operacji w tle, a kontrolki były blokowane na czas pracy. Dialog nadpisania otwiera się poprawnie, gdy nazwa docelowa już istnieje.

## Zachowanie bez LibreOffice

Przed instalacją LibreOffice zestaw testów dawał **50 passed, 4 skipped**. Cztery rzeczywiste testy biurowe były pomijane z przyczyną „LibreOffice is not installed in this environment”. W tym stanie:

- aplikacja się uruchamiała;
- konwersje natywne działały;
- DOCX → PDF, ODT → PDF, DOCX → ODT i ODT → DOCX nie były pokazywane w GUI;
- programowe żądanie konwersji zależnej dawało czytelny błąd z instrukcją instalacji.

Po instalacji LibreOffice wszystkie cztery kontrole działają bez pominięć.

## Zweryfikowane ograniczenia

- Testy sprawdzają treść tekstową i poprawność formatów, ale nie wykonują porównania pikselowego układu PDF.
- Jakość konwersji biurowych zależy od wersji LibreOffice i dostępnych fontów.
- Testy nie obejmują dokumentów chronionych hasłem, makr, podpisów cyfrowych ani PDF/A.
- Dla CSV, JSON i TXT obsługiwany jest wyłącznie UTF-8.
- Konwersja wsadowa i PDF jako format źródłowy nie są zaimplementowane.

## Wniosek

Wszystkie wymagane kierunki działają w bieżącym środowisku. Testy obejmują zarówno ścieżki sukcesu, jak i błędy walidacji, konflikty nazw, brak zależności zewnętrznej, limit czasu i niepoprawny wynik LibreOffice. Zweryfikowane ograniczenia są opisane w README i nie są przedstawiane jako w pełni obsługiwane funkcje.
