from __future__ import annotations

LANGUAGES = {"en": "English", "pl": "Polski"}
DEFAULT_LANGUAGE = "en"

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "app.subtitle": "Local conversion, no uploads · version {version}",
        "theme.light": "Light theme",
        "theme.dark": "Dark theme",
        "source.title": "Source and settings",
        "source.subtitle": "Choose a file, target format, and destination",
        "source.file": "Source file",
        "source.browse": "Browse",
        "tile.name": "Name",
        "tile.format": "Format",
        "tile.size": "Size",
        "tile.time": "Time",
        "source.target": "Target format",
        "source.target.initial": "Select a source file first",
        "source.target.unsupported": "This source format is not supported",
        "source.target.unavailable": (
            "No conversions are available for this format. "
            "Check that LibreOffice is installed."
        ),
        "source.output_dir": "Output folder",
        "source.output_name": "Output name",
        "source.convert": "Convert",
        "source.select_file": "Select source file",
        "source.select_folder": "Select output folder",
        "status.waiting": "Waiting",
        "status.waiting_source": "Waiting for a source file",
        "status.checking": "Checking file...",
        "status.unsupported": "Unsupported format",
        "status.no_targets": "No available target formats",
        "status.ready": "File selected, ready to convert",
        "status.converting": "Converting...",
        "status.done": "Done in {duration:.1f} s · {name}",
        "status.failed": "Conversion failed",
        "status.invalid": "Invalid settings",
        "status.read_error": "Could not read the file",
        "preview.empty": "Result: —",
        "preview.select_target": "Result: select a target format",
        "preview.select_folder": "Result: select an output folder",
        "preview.folder_missing": "Result: folder does not exist — {directory}",
        "preview.check": "Check the settings: {message}",
        "preview.path": "Result: {path}{note}",
        "preview.exists": " · file exists, confirmation will be requested",
        "result.title": "Result",
        "result.subtitle": "The converted file appears here",
        "result.empty.title": "No result yet",
        "result.empty.text": (
            "Choose a source file on the left, select a target format, "
            "and press Convert."
        ),
        "result.empty.directions": (
            "Available directions\n"
            "CSV ↔ JSON · TXT ↔ DOCX · TXT → PDF\n"
            "DOCX/ODT → PDF · DOCX ↔ ODT · ODT → TXT"
        ),
        "result.busy.title": "Converting...",
        "result.busy.text": "Please wait while the file is processed.",
        "result.success.title": "CONVERSION COMPLETE",
        "result.success.note": "The source file was not modified.",
        "result.open_file": "Open file",
        "result.open_folder": "Open folder",
        "result.error.title": "Conversion failed",
        "result.error.details": "Details are available in logs/converter.log.",
        "target.csv.json": "The CSV table becomes an array of JSON objects.",
        "target.json.csv": "The JSON object array becomes a CSV table.",
        "target.txt.docx": "Each text line becomes a paragraph in a Word document.",
        "target.docx.txt": "Paragraph and table text is extracted from the Word document.",
        "target.txt.pdf": "Text is laid out as a Unicode-capable PDF.",
        "target.docx.pdf": "LibreOffice exports the Word document to PDF.",
        "target.odt.pdf": "LibreOffice exports the OpenDocument to PDF.",
        "target.docx.odt": "LibreOffice converts the Word document to ODT.",
        "target.odt.docx": "LibreOffice converts the OpenDocument to Word.",
        "target.odt.txt": "Text is extracted from the OpenDocument with odfpy.",
        "target.default": "Convert {source} → {target}.",
        "dialog.file_exists": "File already exists",
        "dialog.target_exists": "The target file already exists",
        "dialog.overwrite_question": (
            "Overwrite the file, save it under a new name, or cancel?"
        ),
        "dialog.cancel": "Cancel",
        "dialog.save_as": "Save as {name}",
        "dialog.overwrite": "Overwrite",
        "dialog.close": "Close",
        "dialog.continue": "Continue",
        "dialog.missing_settings": "Missing settings",
        "dialog.missing_settings.text": "Select a target format and an output folder.",
        "dialog.could_not_start": "Could not start the conversion",
        "dialog.check_settings": "Check the settings",
        "dialog.unexpected": "Unexpected error",
        "dialog.unexpected.hint": "Details were written to logs/converter.log.",
        "dialog.could_not_read": "Could not read the file",
        "dialog.unsupported": "Unsupported file",
        "dialog.open_file": "Could not open the file",
        "dialog.open_folder": "Could not open the folder",
        "dialog.close_in_progress": "Conversion in progress",
        "dialog.close_in_progress.text": (
            "Close the application? The current operation may be interrupted."
        ),
        "dialog.close_button": "Close",
        "dialog.conversion_failed": "Conversion failed",
        "dialog.invalid_settings": "Invalid settings",
    },
    "pl": {
        "app.subtitle": "Lokalna konwersja, bez wysyłania plików · wersja {version}",
        "theme.light": "Jasny motyw",
        "theme.dark": "Ciemny motyw",
        "source.title": "Źródło i ustawienia",
        "source.subtitle": "Wybierz plik, format docelowy i miejsce zapisu",
        "source.file": "Plik źródłowy",
        "source.browse": "Przeglądaj",
        "tile.name": "Nazwa",
        "tile.format": "Format",
        "tile.size": "Rozmiar",
        "tile.time": "Czas",
        "source.target": "Format docelowy",
        "source.target.initial": "Najpierw wybierz plik źródłowy",
        "source.target.unsupported": "Ten format źródłowy nie jest obsługiwany",
        "source.target.unavailable": (
            "Brak dostępnych konwersji dla tego formatu. "
            "Sprawdź, czy LibreOffice jest zainstalowany."
        ),
        "source.output_dir": "Folder zapisu",
        "source.output_name": "Nazwa pliku wynikowego",
        "source.convert": "Konwertuj",
        "source.select_file": "Wybierz plik źródłowy",
        "source.select_folder": "Wybierz folder zapisu",
        "status.waiting": "Oczekiwanie",
        "status.waiting_source": "Oczekiwanie na plik źródłowy",
        "status.checking": "Sprawdzanie pliku...",
        "status.unsupported": "Nieobsługiwany format",
        "status.no_targets": "Brak dostępnych formatów docelowych",
        "status.ready": "Plik wybrany, gotowy do konwersji",
        "status.converting": "Konwersja...",
        "status.done": "Gotowe w {duration:.1f} s · {name}",
        "status.failed": "Konwersja nie powiodła się",
        "status.invalid": "Nieprawidłowe ustawienia",
        "status.read_error": "Nie można odczytać pliku",
        "preview.empty": "Wynik: —",
        "preview.select_target": "Wynik: wybierz format docelowy",
        "preview.select_folder": "Wynik: wybierz folder zapisu",
        "preview.folder_missing": "Wynik: folder nie istnieje — {directory}",
        "preview.check": "Sprawdź ustawienia: {message}",
        "preview.path": "Wynik: {path}{note}",
        "preview.exists": " · plik istnieje, wymagane będzie potwierdzenie",
        "result.title": "Wynik",
        "result.subtitle": "Przekonwertowany plik pojawi się tutaj",
        "result.empty.title": "Brak wyniku",
        "result.empty.text": (
            "Wybierz plik źródłowy po lewej, wskaż format docelowy "
            "i naciśnij Konwertuj."
        ),
        "result.empty.directions": (
            "Dostępne kierunki\n"
            "CSV ↔ JSON · TXT ↔ DOCX · TXT → PDF\n"
            "DOCX/ODT → PDF · DOCX ↔ ODT · ODT → TXT"
        ),
        "result.busy.title": "Konwersja...",
        "result.busy.text": "Poczekaj, trwa przetwarzanie pliku.",
        "result.success.title": "KONWERSJA ZAKOŃCZONA",
        "result.success.note": "Plik źródłowy nie został zmieniony.",
        "result.open_file": "Otwórz plik",
        "result.open_folder": "Otwórz folder",
        "result.error.title": "Konwersja nie powiodła się",
        "result.error.details": "Szczegóły są dostępne w logs/converter.log.",
        "target.csv.json": "Tabela CSV staje się tablicą obiektów JSON.",
        "target.json.csv": "Tablica obiektów JSON staje się tabelą CSV.",
        "target.txt.docx": "Każdy wiersz tekstu staje się akapitem w dokumencie Word.",
        "target.docx.txt": "Tekst akapitów i tabel jest wyodrębniany z dokumentu Word.",
        "target.txt.pdf": "Tekst jest układany w pliku PDF obsługującym Unicode.",
        "target.docx.pdf": "LibreOffice eksportuje dokument Word do PDF.",
        "target.odt.pdf": "LibreOffice eksportuje OpenDocument do PDF.",
        "target.docx.odt": "LibreOffice konwertuje dokument Word do ODT.",
        "target.odt.docx": "LibreOffice konwertuje OpenDocument do Word.",
        "target.odt.txt": "Tekst jest wyodrębniany z OpenDocument za pomocą odfpy.",
        "target.default": "Konwertuj {source} → {target}.",
        "dialog.file_exists": "Plik już istnieje",
        "dialog.target_exists": "Plik docelowy już istnieje",
        "dialog.overwrite_question": (
            "Nadpisać plik, zapisać pod nową nazwą czy anulować?"
        ),
        "dialog.cancel": "Anuluj",
        "dialog.save_as": "Zapisz jako {name}",
        "dialog.overwrite": "Nadpisz",
        "dialog.close": "Zamknij",
        "dialog.continue": "Kontynuuj",
        "dialog.missing_settings": "Brak ustawień",
        "dialog.missing_settings.text": "Wybierz format docelowy i folder zapisu.",
        "dialog.could_not_start": "Nie można rozpocząć konwersji",
        "dialog.check_settings": "Sprawdź ustawienia",
        "dialog.unexpected": "Nieoczekiwany błąd",
        "dialog.unexpected.hint": "Szczegóły zapisano w logs/converter.log.",
        "dialog.could_not_read": "Nie można odczytać pliku",
        "dialog.unsupported": "Nieobsługiwany plik",
        "dialog.open_file": "Nie można otworzyć pliku",
        "dialog.open_folder": "Nie można otworzyć folderu",
        "dialog.close_in_progress": "Trwa konwersja",
        "dialog.close_in_progress.text": (
            "Zamknąć aplikację? Bieżąca operacja może zostać przerwana."
        ),
        "dialog.close_button": "Zamknij",
        "dialog.conversion_failed": "Konwersja nie powiodła się",
        "dialog.invalid_settings": "Nieprawidłowe ustawienia",
    },
}


def has_translation(language: str, key: str) -> bool:
    return key in _STRINGS.get(language, {}) or key in _STRINGS[DEFAULT_LANGUAGE]


def translate(language: str, key: str, **values) -> str:
    catalog = _STRINGS.get(language, _STRINGS[DEFAULT_LANGUAGE])
    template = catalog.get(key)
    if template is None:
        template = _STRINGS[DEFAULT_LANGUAGE].get(key, key)
    try:
        return template.format(**values)
    except (KeyError, ValueError):
        return template
