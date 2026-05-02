"""Shared helpers for the segment editor addon.

Keeps a single cached `xbmcaddon.Addon()` handle plus a cached copy of the
``enable_verbose_logging`` flag so hot paths don't call the Kodi API on every
log line.
"""
import xbmc  # pyright: ignore[reportMissingImports]
import xbmcaddon  # pyright: ignore[reportMissingImports]
import xbmcvfs  # pyright: ignore[reportMissingImports]

ADDON_ID = "service.segmenteditor"
LOG_PREFIX = "[service.segmenteditor]"

_addon = None
_verbose_cached = None


def get_addon():
    """Return a cached addon handle.

    A single handle is reused across the process; `refresh_addon()` can be
    called if the handle ever needs to be dropped (for example if settings
    change in a way the cached handle does not observe).
    """
    global _addon
    if _addon is None:
        _addon = xbmcaddon.Addon()
    return _addon


def refresh_addon():
    """Drop the cached addon handle so it is re-created on next access."""
    global _addon
    _addon = None


def _read_verbose_setting():
    try:
        return get_addon().getSettingBool("enable_verbose_logging")
    except Exception:
        return False


def refresh_verbose_setting():
    """Re-read the verbose logging flag; call from onSettingsChanged."""
    global _verbose_cached
    _verbose_cached = _read_verbose_setting()
    return _verbose_cached


def log(msg):
    """Log a message if verbose logging is enabled.

    The verbose flag is cached to avoid hitting Kodi settings on every call.
    """
    global _verbose_cached
    if _verbose_cached is None:
        _verbose_cached = _read_verbose_setting()
    if _verbose_cached:
        xbmc.log(f"{LOG_PREFIX} {msg}", xbmc.LOGINFO)


def log_always(msg):
    """Always log a message regardless of verbose setting."""
    xbmc.log(f"{LOG_PREFIX} {msg}", xbmc.LOGINFO)


def log_error(msg):
    """Log an error-level message."""
    xbmc.log(f"{LOG_PREFIX} {msg}", xbmc.LOGERROR)


def notify_open_editor():
    """Open the segment editor from this Python interpreter (keymap RunScript, etc.).

    RunScript runs in a different context than the background service; sending
    NotifyAll alone does not reliably open the UI because only the service
    subscribes to that IPC. Remote triggers should still use JSON-RPC
    ``JSONRPC.NotifyAll`` (see USAGE.md), which the service receives.
    """
    from editor_session import open_segment_editor as _open_editor

    try:
        return _open_editor()
    except Exception as err:
        log_error(f"Failed to open editor: {err}")
        import traceback
        log_error(traceback.format_exc())
        return False


def get_video_file():
    """Return the path of the currently playing video, or None."""
    try:
        player = xbmc.Player()
        # Match Skippy: HasVideo is true during startup/buffering before isPlayingVideo.
        if not (
            player.isPlayingVideo() or xbmc.getCondVisibility("Player.HasVideo")
        ):
            return None
        path = player.getPlayingFile()
    except RuntimeError:
        return None

    if xbmcvfs.exists(path):
        return path
    return None
