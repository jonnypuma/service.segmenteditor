"""
Bridge script to trigger the segment editor from keymap.
This creates a trigger file that the background service monitors.
Uses Kodi's path translation to work on any platform.
"""
import xbmc
import xbmcvfs
import xbmcaddon
import os

try:
    # Get addon path using Kodi's standard method
    addon = xbmcaddon.Addon('service.segmenteditor')
    addon_path = addon.getAddonInfo('path')
    
    # Create trigger file path
    trigger_file = os.path.join(addon_path, 'trigger_editor.txt')
    
    # Create the trigger file
    # Use xbmcvfs for cross-platform compatibility
    try:
        f = xbmcvfs.File(trigger_file, 'w')
        if f:
            f.write('trigger')
            f.close()
            xbmc.log(f"[service.segmenteditor] ✅ Trigger file created: {trigger_file}", xbmc.LOGINFO)
        else:
            xbmc.log(f"[service.segmenteditor] ❌ Could not create trigger file: {trigger_file}", xbmc.LOGERROR)
    except Exception as e:
        xbmc.log(f"[service.segmenteditor] ❌ Error creating trigger file: {e}", xbmc.LOGERROR)
        # Fallback to standard Python file operations if xbmcvfs fails
        try:
            with open(trigger_file, 'w') as f:
                f.write('trigger')
            xbmc.log(f"[service.segmenteditor] ✅ Trigger file created (fallback method): {trigger_file}", xbmc.LOGINFO)
        except Exception as e2:
            xbmc.log(f"[service.segmenteditor] ❌ Fallback method also failed: {e2}", xbmc.LOGERROR)
            
except Exception as e:
    xbmc.log(f"[service.segmenteditor] ❌ Error in trigger.py: {e}", xbmc.LOGERROR)
    import traceback
    xbmc.log(f"[service.segmenteditor] Traceback: {traceback.format_exc()}", xbmc.LOGERROR)

