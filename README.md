# Margin Analyzer

PyQt5 desktop app for the Primary screen: filters, records table, activity log and the
Import / Safe Import / Save / Send actions.

## Run

```
python main.py
```

Use the Anaconda interpreter (`%USERPROFILE%\anaconda3\python.exe`, it already has PyQt5 and
pandas), or any Python 3.8+ after `pip install -r requirements.txt`.

## Project layout

| Path | What goes there |
| --- | --- |
| `main.py` | Entry point |
| `ui/` | Design, edited in Qt Designer: `main_window.ui` (layout, texts, stylesheet), `resources.qrc`, `icons/` |
| `app/` | Qt glue: loads the .ui, runs the buttons in the background, fills and filters the table, shows the logs |
| `packages/` | Logic behind the buttons, one module per button, no PyQt code |

## Change the design

Open `ui/main_window.ui` in Qt Designer (`%USERPROFILE%\anaconda3\Library\bin\designer.exe`).

- Colors, fonts and sizes live in the stylesheet of `MainWindow`
  (right-click the window in Designer > Change styleSheet...).
- Some widgets carry dynamic properties the stylesheet uses: `card` (white cards),
  `role` (`fieldLabel`, `hint`, `separator`) and `variant` (`primary` for the blue button).
- Keep the object names (`importButton`, `tableWidget`, `logView`...): the Python code uses them.
- To add an icon, put the SVG in `ui/icons/` and add it to `resources.qrc` (Designer's resource
  editor does both). `ui/resources_rc.py` is rebuilt automatically the next time you start the app.

## Plug in your logic

Each button calls `run()` in its module, in a background thread:

| Button | Function | Receives | Returns |
| --- | --- | --- | --- |
| Import | `packages/import_data.py` | Primary date | `pandas.DataFrame` shown in the table |
| Safe Import | `packages/safe_import.py` | Primary date, current table | `pandas.DataFrame` shown in the table |
| Save | `packages/save.py` | table, Primary date | nothing |
| Send | `packages/send.py` | table, Primary date | nothing |

Inside `run()`:

- report progress with `progress(percent, "message")`: it drives the progress bar;
- log with `logging.getLogger(__name__)`: messages appear in the Activity log;
- raise an exception on failure: the traceback is logged and the status turns red.

The DataFrame columns become the table columns. The filters look for the columns
`Filecode`, `Desk`, `Root Cause`, `Analyst` and `Booking Date`; if yours are named differently,
update `FILTER_COLUMNS` in `app/main_window.py`.

The current bodies are demos (sample data, simulated steps) marked with `TODO`.
Delete `packages/demo.py` once Import reads your real data.
