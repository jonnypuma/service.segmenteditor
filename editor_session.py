"""Open the segment editor dialog.

Used both by the background service (JSON-RPC / NotifyAll) and by RunScript
entrypoints (keymap, remote key mapped to RunScript). The latter run in a
separate Python context: NotifyAll only reaches the service process, so local
triggers must open the UI directly from this module.
"""
import os

import xbmc
import xbmcgui

from editor_dialog import SegmentEditorDialog
from segment_parser import (
    delete_segment_files,
    parse_chapters,
    parse_edl,
    save_segments,
)
from utils import get_addon, log, log_always, log_error, get_video_file

_editor_active = False


def open_segment_editor(video_path=None):
    """Open the segment editor dialog for the current or specified video."""
    global _editor_active
    log_always("open_segment_editor() called")

    if _editor_active:
        log_always("Editor already open, ignoring request")
        return

    if not video_path:
        video_path = get_video_file()

    if not video_path:
        log_always("No video file available for editing")
        xbmcgui.Dialog().ok("Segment Editor", "No video is currently playing.")
        return

    log_always(f"Opening segment editor for: {os.path.basename(video_path)}")
    _editor_active = True

    try:
        segments = parse_chapters(video_path)
        if not segments:
            segments = parse_edl(video_path)

        current_time = None
        try:
            player = xbmc.Player()
            if player.isPlayingVideo():
                current_time = player.getTime()
        except Exception:
            pass

        addon = get_addon()
        dialog = SegmentEditorDialog(
            "SegmentEditorDialog.xml",
            addon.getAddonInfo("path"),
            "default",
            video_path=video_path,
            segments=segments or [],
            current_time=current_time,
        )
        try:
            dialog.doModal()
        except Exception as dialog_err:
            log_error(f"Error creating/showing dialog: {dialog_err}")
            import traceback
            log_error(f"Traceback: {traceback.format_exc()}")
            raise

        if dialog.segments_modified:
            log("Segments were modified, saving...")
            if dialog.segments:
                edl_ok, xml_ok = save_segments(video_path, dialog.segments)
                if edl_ok or xml_ok:
                    xbmcgui.Dialog().notification(
                        "Segment Editor",
                        "Segments saved successfully",
                        time=2000,
                    )
                else:
                    xbmcgui.Dialog().ok(
                        "Segment Editor",
                        "Failed to save segments. Check file permissions.",
                    )
            else:
                delete_segment_files(video_path)

        del dialog
    except Exception as e:
        log_error(f"Error opening editor: {e}")
        import traceback
        log_error(f"Traceback: {traceback.format_exc()}")
        xbmcgui.Dialog().ok("Segment Editor", f"Error opening editor: {str(e)}")
    finally:
        _editor_active = False
