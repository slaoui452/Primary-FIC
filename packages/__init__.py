"""Logic behind the buttons of the Primary screen, one module per button.

    import_data.py  -> Import
    safe_import.py  -> Safe Import
    save.py         -> Save
    send.py         -> Send

Each module exposes ``run(..., progress=...)``. The UI calls it from a
background thread, so the window stays responsive. Some rules keep this layer
easy to test and reuse:

* no PyQt imports in this folder;
* report progress with ``progress(percent, "what is happening")``;
* log with ``logging.getLogger(__name__)``, and the messages show up in the Activity log;
* raise an exception when something goes wrong, and the UI logs it and shows the error.
"""
