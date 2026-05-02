"""Shared executable entrypoint helpers.

Kodi may invoke this addon via several script files (`default.py`, `main.py`,
or `open_editor.py`) depending on whether the call came from a keymap, RunAddon,
or JSON-RPC. Keep the actual error handling in one place so all paths behave
the same.
"""
from utils import notify_open_editor, log_error


def run(label="entry script"):
    """Open the segment editor (RunScript / RunAddon entry)."""
    try:
        return notify_open_editor()
    except Exception as err:
        log_error(f"Error in {label}: {err}")
        import traceback
        log_error(traceback.format_exc())
        try:
            import xbmcgui
            xbmcgui.Dialog().ok("Segment Editor", f"Error: {err}")
        except Exception:
            pass
        return False
