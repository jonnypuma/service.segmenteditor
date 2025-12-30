"""
Script entry point to open the segment editor.
Can be called from keymap.xml or other addons.
Always uses trigger file method to signal the background service.
"""
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import sys
import os

# Get addon by ID explicitly
try:
    addon = xbmcaddon.Addon('service.segmenteditor')
except:
    # Fallback - try to get current addon
    try:
        addon = xbmcaddon.Addon()
    except:
        xbmc.log("[service.segmenteditor] ❌ CRITICAL: Could not get addon object!", xbmc.LOGERROR)
        xbmcgui.Dialog().ok("Segment Editor", "Error: Could not initialize addon.")
        sys.exit(1)

addon_path = addon.getAddonInfo('path')

# Log for debugging
xbmc.log(f"[service.segmenteditor] 🔔 open_editor.py entry point triggered from: {addon_path}", xbmc.LOGINFO)

# Always use trigger file method to signal the background service
# This prevents multiple service instances from interfering
try:
    trigger_file = os.path.join(addon_path, "trigger_editor.txt")
    # Create trigger file using xbmcvfs for cross-platform compatibility
    try:
        f = xbmcvfs.File(trigger_file, 'w')
        if f:
            f.write('trigger')
            f.close()
            xbmc.log(f"[service.segmenteditor] ✅ Trigger file created: {trigger_file}", xbmc.LOGINFO)
        else:
            xbmc.log(f"[service.segmenteditor] ❌ Failed to create trigger file", xbmc.LOGERROR)
            xbmcgui.Dialog().ok("Segment Editor", "Failed to create trigger file. Check Kodi logs.")
    except Exception as vfs_err:
        # Fallback to standard Python file operations
        xbmc.log(f"[service.segmenteditor] ⚠️ xbmcvfs failed: {vfs_err}, trying fallback", xbmc.LOGWARNING)
        try:
            with open(trigger_file, 'w') as f:
                f.write('trigger')
            xbmc.log(f"[service.segmenteditor] ✅ Trigger file created (fallback): {trigger_file}", xbmc.LOGINFO)
        except Exception as fallback_err:
            xbmc.log(f"[service.segmenteditor] ❌ Fallback also failed: {fallback_err}", xbmc.LOGERROR)
            xbmcgui.Dialog().ok("Segment Editor", f"Error creating trigger file: {str(fallback_err)}")
except Exception as e:
    import traceback
    error_msg = f"Error in open_editor.py: {e}\n{traceback.format_exc()}"
    xbmc.log(f"[service.segmenteditor] ❌ {error_msg}", xbmc.LOGERROR)
    xbmcgui.Dialog().ok("Segment Editor", f"Error: {str(e)}")

