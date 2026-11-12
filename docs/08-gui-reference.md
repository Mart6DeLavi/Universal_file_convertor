# 08 — GUI reference

The interface is implemented in `src/file_converter/gui/`. This page documents the window structure, widget state, event flow, and localization.

## Window

| Property | Value |
|---|---|
| Class | `MainWindow(ctk.CTk)` in `gui/main_window.py` |
| Title | `Universal File Converter` |
| Default size | `1180×720` (`geometry`) |
| Minimum size | `1000×620` (`minsize`) |
| Appearance | dark by default (`ctk.set_appearance_mode("dark")`) |
| Color theme | `green` (`ctk.set_default_color_theme("green")`) |
| Background | `("#eef0f5", "#0f0f12")` |
| Close handler | `WM_DELETE_WINDOW` → `_on_close` |

The window has no scrollable containers. The header spans the top; below it `workspace` uses two equal-weight columns (`uniform="panel"`), each holding a `SectionCard`. Panels expand with the window.

## Layout

```text
row 0  header: title + subtitle | EN/PL | theme switch
row 1  workspace (weight 1)
       ├── column 0: source card
       │     Source file [read-only entry] [Browse]
       │     Name | Format | Size tiles
       │     divider
       │     Target format [option menu]
       │     target description
       │     Output folder [entry] [Browse]
       │     Output name [entry]
       │     result preview
       │     [Convert]
       │     status dot + status text | progress bar + percent
       └── column 1: result card
             one of: empty | busy | success | error
```

## Widgets and state

| Attribute | Type | Purpose |
|---|---|---|
| `source_path_var` / `source_path_entry` | `StringVar` / read-only `CTkEntry` | Selected source path |
| `browse_button` | `CTkButton` | Opens the source file dialog |
| `source_name_label`, `source_format_label`, `source_size_label` | `CTkLabel` | Source tiles |
| `target_var` / `target_menu` | `StringVar` / `CTkOptionMenu` | Target format by display label |
| `target_hint` | `CTkLabel` | Description of the chosen direction |
| `output_dir_var` / `output_dir_entry` / `output_dir_button` | entry + browse | Destination folder |
| `name_var` / `name_entry` | entry | Output file name |
| `preview_label` | `CTkLabel` | Resolved output path / inline validation |
| `convert_button` | `CTkButton` | Starts conversion |
| `status_dot` / `status_label` | `StatusDot` + label | Idle/working/success/error status |
| `progress` / `progress_percent_label` | `CTkProgressBar` + label | Determinate progress in the source panel |
| `result_card` and four frames | `CTkFrame` | Result states |

Internal fields:

| Field | Meaning |
|---|---|
| `_language` | `"en"` or `"pl"`, loaded from config |
| `_source_info` | `SourceInfo` or `None` |
| `_targets` | Available target codes for the current source |
| `_target_labels` | Display label → format code |
| `_busy` | A conversion is running |
| `_closing` | The window is being destroyed |
| `_name_edited` | The user changed the name manually |
| `_output_dir_user_set` | The user chose/typed a folder |
| `_last_auto_name` | Last generated name (bookkeeping) |
| `_queue` | Worker → UI event queue |
| `_thread` | Current worker thread |
| `_last_result_path` | Path for the open buttons |
| `_last_result` | `ConversionResult` or `None` |
| `_last_error` | `(message, hint)` or `None` |
| `_poll_id`, `_progress_after_id` | Scheduled `after` callbacks |
| `_progress_value`, `_progress_target` | Displayed and target progress |
| `_busy_started` | Monotonic timestamp for the estimate |

## Result states

`_show_result_state(name)` calls `grid_remove()` on all four frames and `grid()` on the chosen one.

### empty

Shown at startup, after a new source is selected, and on reset:

- **No result yet**
- instruction to choose a file, target, and press Convert
- the list of available directions (localized)

### busy

- **Converting...**
- large percentage label (`busy_percent_label`)
- hint to wait

### success

- **CONVERSION COMPLETE**
- output file name (`result_name_label`)
- full path (`result_path_label`)
- **Format**, **Size**, **Time** tiles
- **Open file** and **Open folder**
- note that the source was not modified

### error

- **Conversion failed**
- `error_message_label` (the exception message)
- `error_hint_label` (the hint, if any)
- note pointing to `logs/converter.log`

## Event flow

### Source selection

`_browse_source` → `filedialog.askopenfilename` with `SUPPORTED_FILETYPES` → `_apply_source(path)`.

`_apply_source`:

1. resets `_source_info`, `_targets`, `_target_labels`, `_name_edited`, last result/error, and progress;
2. shows the empty result state and fills the name tile immediately;
3. reads `SourceInfo.from_path` (read error → dialog + red status);
4. calls `validators.validate_source` (unsupported → dialog + red status);
5. calls `registry.available_targets(extension)`:
   - none → hint explaining that no conversions are available (mentions LibreOffice);
6. fills the menu with `FORMAT_LABELS` values, selects the first, and triggers `_on_target_change(..., reset_name=True)`;
7. sets the output folder to the source folder unless `_output_dir_user_set` is true or the field is empty;
8. updates the preview and sets status *File selected, ready to convert*.

### Target change

`_on_target_change(choice, reset_name=False)`:

- maps the label back to a format code;
- updates the direction description (localized `target.<source>.<target>` key, else a generic template);
- regenerates the output name if `reset_name` or the user has not edited it;
- refreshes the preview.

### Name and folder edits

- `name_entry` `<KeyRelease>` → `_name_edited = True` + preview.
- `output_dir_entry` `<KeyRelease>` → `_output_dir_user_set = True` + preview.
- Browsing a folder also sets `_output_dir_user_set`.

### Preview

`_update_preview` chooses the first applicable message:

| Condition | Preview |
|---|---|
| no source | *Result: —* |
| no target | *Result: select a target format* |
| no folder | *Result: select an output folder* |
| folder does not exist | orange warning with the path |
| name/path invalid | orange *Check the settings: …* |
| otherwise | *Result: <full path>* + *file exists…* note |

It also enables or disables **Convert** through `_set_controls_state`.

### Convert

`_start_conversion`:

1. ignores the click while busy or without a source;
2. requires a target and folder, otherwise a message dialog;
3. builds `ConversionRequest` from the fields;
4. validates (`validate_request`); on `OutputConflictError` opens the overwrite dialog and applies the decision; on other errors shows a dialog and turns the status red;
5. clears last result/error, calls `_set_busy(True)`, and starts a daemon thread running `_run_conversion`.

`_run_conversion` calls `service.execute(request, progress=queue.put)` and pushes `("success", result)` or `("error", exc)`.

`_poll_queue` runs on the main thread every 100 ms and dispatches events:

- `progress` → `_set_progress_target`;
- `success` → `_finish_success` (fills the success card, sets 100%, status *Done in N s · name*);
- `error` → `_finish_error` (error card, status *Conversion failed*, dialog for unexpected errors).

### Controls during conversion

`_set_controls_state` disables browsing, folder entry, name entry, and the target menu while `_busy`. **Convert** is enabled only when the current inputs produce a valid path and no conversion is running. Its colors switch between the accent and the disabled accent.

## Progress animation

The worker reports coarse milestones. The UI makes them smooth and monotonic:

- `_set_progress_target` never lowers the target;
- while busy, `_tick_progress` raises the target with `0.9 - 0.85 * exp(-elapsed / 0.8)`, so the bar keeps moving during long conversions but never reaches 90% on its own;
- every 30 ms the displayed value moves 28% of the remaining distance;
- `_complete_progress` forces 100% on success;
- `_reset_progress` cancels the animation and resets to 0;
- both the small bar and the large busy percentage are updated in `_set_progress_display`.

## Dialogs

`gui/dialogs.py` provides modal `CTkToplevel` windows:

| Class | Size | Result |
|---|---|---|
| `OverwriteDialog` | 540×250 | `"unique"`, `"overwrite"`, or `None` |
| `ConfirmDialog` | 460×210 | `"confirm"` or `None` |
| `MessageDialog` | 560×230 (300 with hint) | closes |

Common behavior (`_Modal`):

- centered over the parent, one-third down;
- `transient(parent)`, not resizable;
- `grab_set()` and `focus_force()` after 20 ms;
- closing the window is equivalent to Cancel.

Helpers block the caller with `parent.wait_window(dialog)`:

```python
decision = ask_overwrite(parent, path, suggested, language)
confirmed = ask_confirm(parent, title, message, confirm_text="Close", language=language)
show_message(parent, title, message, hint="", error=False, language=language)
```

The overwrite dialog offers:

- **Cancel** (`result = None`);
- **Save as `<suggested name>`** (`"unique"`);
- **Overwrite** (`"overwrite"`, red button).

## Theme

`_toggle_theme` flips `ctk.set_appearance_mode` between light and dark and updates the switch label. In dark mode the switch says *Light theme* (the action), in light mode *Dark theme*. The choice is not saved to disk; each launch starts in dark mode.

## Language and i18n

- `_language` is loaded with `config.get_language()` during construction.
- The header segmented button holds `["EN", "PL"]`; selection calls `_on_language_change`.
- While busy, the switch is reverted and ignored.
- Otherwise the code is persisted with `config.set_language`, `_language` is updated, and `_rebuild_ui()` runs.
- `_rebuild_ui` saves the current state (source path, target, folder, name, flags, last result/error), cancels callbacks, drains the queue, destroys all children, rebuilds the layout, restarts polling, restores the state, and refreshes controls.

The `translate` function uses `_STRINGS[language]`, falls back to English, then to the key. Placeholders are formatted with `str.format`; a missing placeholder returns the raw template instead of raising.

Key naming:

| Prefix | Used for |
|---|---|
| `app.*` | Header text |
| `theme.*` | Theme switch labels |
| `source.*` | Source panel labels and status hints |
| `tile.*` | Tile captions |
| `status.*` | Status line |
| `preview.*` | Preview messages |
| `result.*` | Result panel |
| `target.<source>.<target>` | Direction descriptions |
| `target.default` | Generic description |
| `dialog.*` | Dialog titles, buttons, messages |

To add a language:

1. add the code and name to `LANGUAGES` and a full catalog to `_STRINGS`;
2. allow the code in `config.get_language` / `set_language`;
3. add the button value and mapping in `MainWindow` (`["EN", "PL"]` and `_on_language_change`);
4. keep the key sets identical — `tests/test_i18n.py` checks catalog parity.

## Palette

`gui/components.py` defines light/dark tuples:

| Constant | Light | Dark | Use |
|---|---|---|---|
| `CARD_COLOR` | `#ffffff` | `#1a1a1e` | Card background |
| `CARD_BORDER` | `#d9d9e3` | `#2b2b31` | Card border |
| `MUTED` | `#6b6b76` | `#9a9aa5` | Secondary text |
| `ACCENT` | `#2f6f4e` | `#357a57` | Primary buttons, progress |
| `ACCENT_HOVER` | `#285c41` | `#2f6f4e` | Primary hover |
| `ACCENT_TEXT` | `#ffffff` | `#f0fdf4` | Text on accent |
| `ACCENT_FOREGROUND` | `#2f6f4e` | `#6ee7b7` | Accent-colored text |
| `ACCENT_SELECTED` | `#d7e8dd` | `#24463a` | Selected segments |
| `ACCENT_SELECTED_HOVER` | `#c4ddce` | `#2d5748` | Selected hover |
| `ACCENT_DISABLED` | `#d7e5dd` | `#213229` | Disabled primary |
| `ACCENT_DISABLED_TEXT` | `#5f7669` | `#8ba295` | Disabled text |
| `SECONDARY` | `#eef0f5` | `#24242a` | Secondary buttons |
| `SECONDARY_HOVER` | `#e2e5ec` | `#2f2f37` | Secondary hover |
| `SECONDARY_TEXT` | `#333333` | `#dddddd` | Secondary text |
| `SUCCESS` | `#15803d` | `#4ade80` | Success dot |

`StatusDot` states: `idle` (grey), `working` (amber), `success` (green), `error` (red).

## Closing

`_on_close`:

- while busy, asks for confirmation; declining keeps the window open;
- sets `_closing`, cancels polling and progress callbacks, and destroys the window;
- the daemon worker cannot block process exit. A conversion in progress may be interrupted; its temporary directory is cleaned up by the OS/Python when possible, and no partial destination file is published.
