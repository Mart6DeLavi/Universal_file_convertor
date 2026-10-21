# Universal File Converter

[English](README.md) | [Polski](README.pl.md)

Lokalna aplikacja desktopowa do konwersji arkuszy, plików tekstowych i dokumentów biurowych. Pliki nie są nigdzie wysyłane; aplikacja pokazuje wyłącznie rzeczywiście obsługiwane kierunki i nigdy nie nadpisuje istniejącego pliku bez potwierdzenia.

Aplikacja jest napisana w Pythonie z interfejsem CustomTkinter. Konwersje biurowe wykonuje LibreOffice w trybie headless.

## Przeznaczenie

Użytkownik wybiera plik źródłowy i folder docelowy, widzi formaty dostępne dla tego pliku, uruchamia konwersję i otrzymuje gotowy wynik. Cały scenariusz odbywa się w GUI, bez terminala. Jeśli LibreOffice nie jest zainstalowany, powiązane kierunki są ukryte i nie są zgłaszane jako dostępne.

## Funkcje

- Dwukolumnowy interfejs: źródło i ustawienia konwersji po lewej, wynik po prawej.
- Brak przewijania: cały przepływ pracy jest widoczny przy domyślnym i minimalnym rozmiarze okna.
- Wybór pliku źródłowego i folderu docelowego przez systemowe okna dialogowe.
- Informacje o źródle: nazwa, ścieżka, format i rozmiar.
- Dynamiczna lista formatów docelowych zależna od pliku źródłowego i zainstalowanych zależności.
- Konwersja w tle: interfejs pozostaje responsywny.
- Wskaźnik postępu, czytelny status końcowy i szczegółowa karta wyniku.
- Ochrona przed przypadkowym nadpisaniem: potwierdzenie, automatyczna unikalna nazwa lub anulowanie.
- Walidacja danych wejściowych, folderu docelowego, zależności i wyniku konwersji.
- Zachowanie polskich, cyrylickich i innych znaków Unicode.
- Otwieranie przekonwertowanego pliku lub jego folderu bezpośrednio z interfejsu.
- Logowanie operacji i błędów.
- Motywy ciemny i jasny.
- Angielski interfejs użytkownika.

## Obsługiwane formaty

Formaty źródłowe: CSV, JSON, TXT, DOCX, ODT.

Formaty docelowe: CSV, JSON, TXT, DOCX, ODT, PDF.

PDF jest obsługiwany tylko jako format docelowy. Wyodrębnianie treści z PDF nie jest zaimplementowane.

## Matryca konwersji

| # | Źródło | Cel | Silnik | Co jest zachowywane | Ograniczenia |
|---:|---|---|---|---|---|
| 1 | CSV | JSON | `csv`, `json` | Nagłówki, kolejność kolumn i kluczy, Unicode, puste ciągi | Jedna tabela; typy nie są rozpoznawane automatycznie |
| 2 | JSON | CSV | `csv`, `json` | Tablica obiektów, połączony zbiór kluczy, Unicode | Poziom najwyższy musi być tablicą obiektów; zagnieżdżone wartości są serializowane do komórki |
| 3 | TXT | DOCX | `python-docx` | Każdy wiersz jako osobny akapit; Unicode | Podziały wierszy są granicami akapitów; formatowanie nie jest tworzone |
| 4 | DOCX | TXT | `python-docx` | Tekst akapitów i tabel w kolejności dokumentu | Style, obrazy, nagłówki, stopki i znaczniki nie są przenoszone |
| 5 | TXT | PDF | `reportlab` | Tekst, Unicode, zawijanie długich wierszy, dzielenie na strony | Podstawowe marginesy A4; obrazy, linki i rich text nie są obsługiwane |
| 6 | DOCX | PDF | LibreOffice | Układ i formatowanie w granicach możliwości LibreOffice | Wymaga LibreOffice |
| 7 | ODT | PDF | LibreOffice | Układ i formatowanie w granicach możliwości LibreOffice | Wymaga LibreOffice |
| 8 | DOCX | ODT | LibreOffice | Struktura i formatowanie dokumentu | Wymaga LibreOffice |
| 9 | ODT | DOCX | LibreOffice | Struktura i formatowanie dokumentu | Wymaga LibreOffice |
| 10 | ODT | TXT | `odfpy` | Tekst akapitów, nagłówków, list i tabel | Formatowanie i obiekty nietekstowe nie są przenoszone |

Wszystkie dziesięć kierunków jest zarejestrowanych w rejestrze konwerterów. Kierunki 6–9 stają się widoczne w GUI tylko wtedy, gdy LibreOffice jest dostępny.

## Semantyka CSV → JSON

- Kodowanie to UTF-8; BOM jest akceptowany przez `utf-8-sig`.
- Pierwszy niepusty wiersz jest traktowany jako wiersz nagłówków.
- Separator jest wykrywany automatycznie spośród `,`, `;`, tabulatora i `|`. Można go ustawić jawnie zmienną środowiskową `UFC_CSV_DELIMITER` (jeden znak; dla tabulatora użyj `\t`).
- Każdy wiersz danych staje się obiektem JSON. Kolejność kluczy odpowiada kolejności kolumn.
- Wszystkie wartości pozostają ciągami znaków. Liczby, daty, `true`/`false` i `null` nie są rozpoznawane automatycznie.
- Puste pole pozostaje pustym ciągiem.
- Obsługiwane są cudzysłowy, przecinki wewnątrz wartości i pola wielowierszowe.
- Puste i zduplikowane nagłówki są odrzucane, ponieważ konwersja byłaby niejednoznaczna.
- Każdy wiersz musi mieć tyle samo pól, ile jest nagłówków.
- Pusty plik, plik bez nagłówków i plik bez wierszy danych są błędami.
- Wynik jest zapisywany jako tablica JSON z wcięciem dwóch spacji i bez kodowania Unicode w formie ASCII.

Przykład:

```csv
imię,nazwisko,miasto,uwagi
Jan,Kowalski,Łódź,"Zażółć gęślą jaźń"
Anna,Nowak,Kraków,
```

```json
[
  {
    "imię": "Jan",
    "nazwisko": "Kowalski",
    "miasto": "Łódź",
    "uwagi": "Zażółć gęślą jaźń"
  },
  {
    "imię": "Anna",
    "nazwisko": "Nowak",
    "miasto": "Kraków",
    "uwagi": ""
  }
]
```

## Semantyka JSON → CSV

- Poziom najwyższy musi być tablicą obiektów JSON. Pusta tablica jest poprawna i tworzy pusty plik CSV.
- Każdy element tablicy musi być obiektem. Tablice wartości prostych i tablice mieszane są odrzucane.
- Nagłówki są tworzone z kluczy w kolejności pierwszego wystąpienia.
- Brakujący klucz staje się pustą komórką.
- Zagnieżdżone obiekty i tablice są zapisywane w komórce jako kompaktowy ciąg JSON.
- `true` i `false` są zapisywane jako `true` i `false`; `null` staje się pustą komórką.
- Niepoprawny JSON powoduje kontrolowany błąd z numerem wiersza i kolumny.
- CSV jest zapisywany jako UTF-8 z `newline=""`, więc cudzysłowy i podziały wierszy są poprawnie escapowane.

Przykład:

```json
[
  {"b": 1, "a": "Żółw", "nested": {"x": 1}},
  {"a": "Zażółć gęślą jaźń", "c": true}
]
```

```csv
b,a,nested,c
1,Żółw,"{""x"":1}",
,Zażółć gęślą jaźń,,true
```

## Interfejs

Główne okno zawiera:

- nagłówek z nazwą aplikacji, wersją i przełącznikiem motywu;
- lewy panel z plikiem źródłowym, informacjami o źródle, formatem docelowym, folderem docelowym, nazwą wyniku, podglądem, przyciskiem Convert i statusem postępu;
- prawy panel z pustym stanem przed konwersją, stanem sukcesu z nazwą wyniku, pełną ścieżką, formatem, rozmiarem, czasem trwania i przyciskami otwierania albo stanem błędu z podpowiedzią.

Układ nie zawiera przewijanych kontenerów. Okno otwiera się w rozmiarze `1180x720` i pozostaje użyteczne przy minimalnym rozmiarze `1000x620`. Długie ścieżki zawijają się w etykietach, zamiast wypychać kontrolki poza widok.

Konwersja działa w wątku tle. Aktualizacje widżetów trafiają do wątku głównego przez kolejkę, więc okno się nie zawiesza.

## Architektura

```text
FileConvertor/
├── app.py                         # punkt wejścia, uruchomienie GUI
├── requirements.txt               # zależności Pythona
├── README.md                      # dokumentacja angielska
├── README.pl.md                   # dokumentacja polska
├── PLAN.md                        # dostarczone zadanie
├── docs/                          # wewnętrzne notatki implementacyjne
├── logs/                          # logi aplikacji
├── reports/
│   ├── test_report.md             # raport testów po angielsku
│   └── test_report.pl.md          # raport testów po polsku
├── src/
│   └── file_converter/
│       ├── config.py              # stałe, formaty, ścieżka LibreOffice
│       ├── exceptions.py          # wspólna hierarchia błędów
│       ├── logging_config.py      # rotowany logger plikowy
│       ├── models.py              # modele żądania, wyniku i źródła
│       ├── registry.py            # rejestr konwerterów i dostępne cele
│       ├── validators.py          # walidacja żądania i ścieżek
│       ├── service.py             # wykonanie, folder tymczasowy, zapis atomowy
│       ├── converters/
│       │   ├── csv_json.py        # CSV ↔ JSON
│       │   ├── text_converters.py # TXT, DOCX, ODT, PDF
│       │   ├── document_converters.py # wrappery konwersji biurowych
│       │   └── libreoffice.py     # integracja LibreOffice w trybie headless
│       ├── gui/
│       │   ├── main_window.py     # główne okno i operacje w tle
│       │   ├── components.py      # karty i wskaźnik statusu
│       │   └── dialogs.py         # dialogi nadpisania i komunikatów
│       └── utils/
│           ├── paths.py           # nazwy, konflikty, prawa zapisu
│           └── platform_utils.py  # otwieranie pliku i folderu
├── tests/                         # zestaw pytest
└── test_data/                     # przykładowe pliki i oczekiwane wyniki
```

Przepływ wykonania: GUI → walidatory → rejestr → serwis → konkretny konwerter. Serwis tworzy folder tymczasowy w katalogu docelowym, sprawdza wynik i dopiero potem atomowo zastępuje plik docelowy przez `os.replace`. Plik źródłowy nigdy nie jest zmieniany.

## Wymagania

- Python 3.11 lub nowszy. Projekt sprawdzono na Pythonie 3.14.8.
- Tk 8.6 lub nowszy. CustomTkinter wymaga Pythona zbudowanego z obsługą Tk.
- macOS, Windows lub Linux.
- LibreOffice tylko dla DOCX → PDF, ODT → PDF, DOCX → ODT i ODT → DOCX.

## Instalacja zależności Pythona

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Jeśli na macOS używasz Pythona z Homebrew i przy uruchomieniu pojawia się błąd `_tkinter`, zainstaluj Tk dla odpowiedniej wersji Pythona:

```bash
brew install python-tk@3.14
```

Na Debian/Ubuntu:

```bash
sudo apt install python3-tk
```

## Instalacja LibreOffice

LibreOffice jest potrzebny dla czterech kierunków biurowych. Bez niego aplikacja nadal działa, ale te kierunki są ukryte.

macOS:

```bash
brew install --cask libreoffice
```

Alternatywnie pobierz instalator ze strony [libreoffice.org](https://www.libreoffice.org/download/) i przeciągnij LibreOffice do `/Applications`.

Windows:

Pobierz i zainstaluj LibreOffice ze strony [libreoffice.org](https://www.libreoffice.org/download/). Plik wykonywalny zwykle znajduje się pod:

```text
C:\Program Files\LibreOffice\program\soffice.exe
```

Debian/Ubuntu:

```bash
sudo apt update
sudo apt install libreoffice
```

Fedora:

```bash
sudo dnf install libreoffice
```

Arch Linux:

```bash
sudo pacman -S libreoffice-fresh
```

Sprawdzenie instalacji:

```bash
soffice --version
```

Na macOS można sprawdzić pakiet aplikacji bezpośrednio:

```bash
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --version
```

### Konfiguracja ścieżki do LibreOffice

Aplikacja szuka `soffice` w następującej kolejności:

1. Zmienna środowiskowa `UFC_SOFFICE`.
2. Zmienna środowiskowa `LIBREOFFICE_PATH`.
3. Klucz `soffice_path` w pliku `~/.config/universal-file-converter/config.json`.
4. Polecenia `soffice` i `libreoffice` w `PATH`.
5. Standardowe katalogi instalacji na macOS, Windows i Linuksie.

Przykład dla macOS/Linux:

```bash
export UFC_SOFFICE="/Applications/LibreOffice.app/Contents/MacOS/soffice"
```

Przykład dla Windows PowerShell:

```powershell
$env:UFC_SOFFICE = "C:\Program Files\LibreOffice\program\soffice.exe"
```

Przykład `config.json`:

```json
{
  "soffice_path": "/Applications/LibreOffice.app/Contents/MacOS/soffice"
}
```

Lokalizacja pliku konfiguracji: `~/.config/universal-file-converter/config.json`. W systemie Windows używany jest katalog domowy bieżącego użytkownika.

## Uruchomienie aplikacji

Z katalogu głównego projektu:

```bash
python app.py
```

Jeśli środowisko wirtualne nie jest aktywne:

```bash
.venv/bin/python app.py
```

Aby dodatkowo wypisywać log w konsoli:

```bash
UFC_LOG_CONSOLE=1 python app.py
```

## Uruchamianie testów

```bash
python -m pytest -v
```

Bez LibreOffice uruchamiają się wszystkie testy natywne, a cztery rzeczywiste testy biurowe są pomijane z podaniem przyczyny. Po zainstalowaniu LibreOffice uruchamia się cały zestaw.

Aktualny wynik na macOS z LibreOffice 26.8.1: **54 passed**. Szczegóły w [`reports/test_report.pl.md`](reports/test_report.pl.md).

## Przykłady i dane testowe

Katalog `test_data/` zawiera:

- `sample.csv` — Unicode, puste pole, przecinek, cudzysłowy i wartość wielowierszowa;
- `sample.json` — zagnieżdżony obiekt, brakujący klucz i wartości logiczne;
- `sample.txt` — tekst polski i cyrylicki z pustymi wierszami;
- `sample.docx` — nagłówek, akapity, tabela i Unicode;
- `sample.odt` — akapity, tabela i Unicode;
- `README.md` — oczekiwane wyniki dla każdego pliku.

Szybka kontrola przez GUI:

1. Uruchom `python app.py`.
2. Wybierz `test_data/sample.csv`.
3. Sprawdź, że dostępny jest tylko JSON.
4. Wybierz folder docelowy i naciśnij **Convert**.
5. Otwórz wynik przyciskiem **Open file**.
6. Powtórz dla `sample.docx`: TXT, ODT i PDF powinny być dostępne, gdy LibreOffice jest zainstalowany.

## Obsługa błędów i bezpieczeństwo

- Sprawdzane jest istnienie pliku źródłowego, jego typ i obsługiwane rozszerzenie.
- Format docelowy musi być zarejestrowany, a jego zależność dostępna.
- Katalog docelowy musi istnieć i być zapisywalny.
- Istniejący plik nigdy nie jest nadpisywany bez wyraźnego potwierdzenia. Dialog oferuje nadpisanie, unikalną nazwę w rodzaju `nazwa (1).ext` albo anulowanie.
- Niepoprawne nazwy plików, niezgodność rozszerzenia oraz identyczne ścieżki źródłowa i docelowa są odrzucane przed rozpoczęciem konwersji.
- Konwersja odbywa się w folderze tymczasowym wewnątrz katalogu docelowego. Plik końcowy pojawia się dopiero po pomyślnej weryfikacji.
- Konwerter musi utworzyć niepusty plik (z wyjątkiem pustej tablicy JSON, która staje się pustym CSV).
- Sprawdzany jest kod wyjścia LibreOffice, limit 120 sekund oraz istnienie i rozmiar wyniku; `stdout` i `stderr` są zachowywane.
- LibreOffice działa z izolowanym profilem tymczasowym, aby nie kolidować z już otwartą instancją.
- Procesy zewnętrzne są uruchamiane listą argumentów z `shell=False`.
- Błędy są pokazywane w GUI z wyjaśnieniem i zapisywane w logu. Aplikacja nigdy nie zgłasza sukcesu, jeśli plik nie został utworzony.
- Plik źródłowy jest otwierany tylko do odczytu i nigdy nie jest zmieniany.

## Logowanie

Plik logu: `logs/converter.log`.

`RotatingFileHandler` utrzymuje pliki do 1 MB z trzema kopiami zapasowymi. Log zawiera rozpoczęcie konwersji, źródło, format docelowy, wynik, czas trwania i wyjątki.

Jeśli katalog logów jest niedostępny, aplikacja działa dalej i nie kończy się z powodu błędu logowania.

## Znane ograniczenia

- Jedna operacja przetwarza jeden plik; konwersja wsadowa nie jest zaimplementowana.
- Obsługiwane są tylko wymienione kierunki. PDF nie jest formatem źródłowym.
- Stary format `.doc` nie jest obsługiwany; używane są `.docx` i `.odt`.
- CSV i JSON są czytane tylko jako UTF-8 (BOM jest dozwolony). Inne kodowania trzeba najpierw przekonwertować.
- CSV używa jednego separatora. Można go ustawić przez `UFC_CSV_DELIMITER`, ale nie przez GUI.
- JSON → CSV nie rozwija zagnieżdżonych struktur na osobne kolumny; serializuje je do komórki.
- TXT → DOCX nie tworzy stylów, list ani tabel: każdy wiersz staje się akapitem.
- DOCX → TXT i ODT → TXT wyodrębniają tylko tekst; formatowanie, obrazy, nagłówki, stopki i przypisy nie są zachowywane.
- TXT → PDF tworzy prosty dokument A4 bez rich text. Dla Unicode używa pierwszego dostępnego systemowego fontu Arial/DejaVu/Liberation.
- Jakość DOCX/ODT → PDF i DOCX ↔ ODT zależy od zainstalowanej wersji LibreOffice. Złożone fonty, makra i obiekty zewnętrzne mogą wyglądać inaczej.
- Konwersje biurowe są ograniczone limitem 120 sekund.
- Hasła, podpisy cyfrowe i PDF/A nie są obsługiwane.
- Aplikacja nie wysyła plików do sieci i nie korzysta z usług chmurowych.

## Biblioteki i komponenty zewnętrzne

- [CustomTkinter](https://customtkinter.tomschimansky.com/) — interfejs desktopowy.
- [python-docx](https://python-docx.readthedocs.io/) — odczyt i tworzenie DOCX.
- [odfpy](https://github.com/eea/odfpy) — odczyt ODT.
- [ReportLab](https://www.reportlab.com/opensource/) — tworzenie PDF.
- [Pillow](https://python-pillow.org/) — zależność stosu graficznego.
- [pypdf](https://pypdf.readthedocs.io/) — weryfikacja PDF w testach.
- [pytest](https://pytest.org/) — testy automatyczne.
- [LibreOffice](https://www.libreoffice.org/) — konwersje biurowe w trybie headless.
- Standardowa biblioteka Pythona: `csv`, `json`, `subprocess`, `tempfile`, `logging`, `pathlib`, `tkinter`.

## Wykorzystanie AI

Projekt zrealizowano z pomocą asystenta AI opencode. Wygenerowany kod zweryfikowano testami automatycznymi, ręcznymi scenariuszami GUI i rzeczywistymi konwersjami plików. Wszystkie ograniczenia i nieweryfikowane w danym środowisku możliwości są opisane wprost; aplikacja nie przedstawia niedostępnych konwersji jako działających.

## Autor

Mart6DeLavi, akademicki projekt programistyczny.
