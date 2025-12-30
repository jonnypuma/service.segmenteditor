import xbmc
import xbmcaddon
import xbmcvfs

def get_addon():
    """Get the addon instance"""
    return xbmcaddon.Addon()

def log(msg):
    """Log a message if verbose logging is enabled"""
    addon = get_addon()
    if addon.getSettingBool("enable_verbose_logging"):
        xbmc.log(f"[{addon.getAddonInfo('id')}] {msg}", xbmc.LOGINFO)

def log_always(msg):
    """Always log a message"""
    addon = get_addon()
    xbmc.log(f"[{addon.getAddonInfo('id')}] {msg}", xbmc.LOGINFO)

def get_video_file():
    """Get the currently playing video file path"""
    try:
        import xbmc
        player = xbmc.Player()
        if not player.isPlayingVideo():
            return None
        path = player.getPlayingFile()
    except RuntimeError:
        return None
    
    if xbmcvfs.exists(path):
        return path
    
    return None

