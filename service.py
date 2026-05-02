"""Background service for service.segmenteditor.

The service:

* watches for the currently playing video,
* re-generates the userdata keymap.xml when the shortcut setting changes,
* listens for the ``open_segment_editor`` NotifyAll IPC message (JSON-RPC or
  ``executebuiltin`` from other addons) and opens the editor in that process.

``RunScript(service.segmenteditor)`` (keyboard shortcut and similar) runs in a
separate Python context and opens the editor via ``editor_session`` directly;
it does not rely on NotifyAll reaching this process.

External triggers (SSH, JSON-RPC, other addons) can send ``JSONRPC.NotifyAll``
with sender ``service.segmenteditor`` and message ``open_segment_editor``, or
call ``RunScript(service.segmenteditor)``.
"""
import os

import xbmc

from editor_session import open_segment_editor
from keymap_utils import update_keymap_file
from utils import (
    ADDON_ID,
    get_addon,
    log,
    log_always,
    log_error,
    get_video_file,
    refresh_verbose_setting,
)


class PlaybackMonitor(xbmc.Monitor):
    def __init__(self):
        super().__init__()
        self.last_video = None
        self.last_shortcut_key = None

    def onSettingsChanged(self):
        refresh_verbose_setting()
        try:
            addon = get_addon()
            current_key = (addon.getSetting("editor_shortcut_key") or "").strip().lower()
            if current_key != self.last_shortcut_key:
                log_always(f"Shortcut key setting changed to {current_key!r}")
                self.last_shortcut_key = current_key
                update_keymap_file()
        except Exception as e:
            log(f"Error handling settings change: {e}")

    def onNotification(self, sender, method, data):
        try:
            # Filter the noisy library/GUI notifications.
            ignored_methods = {
                "AudioLibrary.OnUpdate",
                "VideoLibrary.OnUpdate",
                "GUI.OnScreensaverActivated",
                "GUI.OnScreensaverDeactivated",
                "VideoLibrary.OnScanStarted",
                "VideoLibrary.OnScanFinished",
                "AudioLibrary.OnScanStarted",
                "AudioLibrary.OnScanFinished",
            }
            if method in ignored_methods:
                return

            log(f"Notification received: sender={sender}, method={method}, data={data}")

            try:
                if isinstance(data, str):
                    data_lower = data.lower()
                elif data is not None:
                    data_lower = str(data).lower()
                else:
                    data_lower = ""
            except Exception:
                data_lower = ""

            # Depending on Kodi version and caller, NotifyAll can arrive as either
            # method="open_segment_editor" with sender set, or as
            # method="<flag>.open_segment_editor" (see XBPython::Announce).
            if (
                (sender == ADDON_ID and method == "open_segment_editor")
                or method == "open_segment_editor"
                or method == "Other.open_segment_editor"
                or method == f"{ADDON_ID}.open_segment_editor"
                or method.endswith(".open_segment_editor")
                or "open_segment_editor" in data_lower
            ):
                log_always("Open editor notification detected")
                open_segment_editor()
        except Exception as e:
            log_error(f"onNotification handler error: {e}")


monitor = PlaybackMonitor()
player = xbmc.Player()


def _main():
    log_always("Segment Editor service started")

    addon = get_addon()
    if not addon:
        log_error("CRITICAL: Could not get addon object!")
        return

    refresh_verbose_setting()

    shortcut_key = (addon.getSetting("editor_shortcut_key") or "").strip().lower()
    monitor.last_shortcut_key = shortcut_key if shortcut_key else "e"
    log_always(f"Keyboard shortcut key: {monitor.last_shortcut_key!r}")

    if update_keymap_file():
        log_always("Keymap file updated successfully")
    else:
        log_always("Keymap file update failed - you may need to manually edit keymap.xml")

    # JSON-RPC NotifyAll is handled in PlaybackMonitor.onNotification.
    # The main loop just keeps track of the currently playing video.
    while not monitor.abortRequested():
        try:
            if player.isPlayingVideo():
                video = get_video_file()
                if video and video != monitor.last_video:
                    log(f"New video detected: {os.path.basename(video)}")
                    monitor.last_video = video
        except Exception as err:
            log(f"Error in monitor loop: {err}")

        # Use waitForAbort so the service exits promptly on shutdown.
        if monitor.waitForAbort(1.0):
            break

    log_always("Abort requested - exiting monitor loop")


try:
    _main()
except Exception as critical_err:
    try:
        xbmc.log(
            f"[{ADDON_ID}] CRITICAL SERVICE STARTUP ERROR: {critical_err}",
            xbmc.LOGERROR,
        )
        import traceback
        xbmc.log(f"[{ADDON_ID}] Traceback: {traceback.format_exc()}", xbmc.LOGERROR)
    except Exception:
        pass
