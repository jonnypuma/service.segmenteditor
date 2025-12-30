import os
import time
import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import json

from segment_parser import parse_edl, parse_chapters, save_edl, save_chapters, SegmentItem
from editor_dialog import SegmentEditorDialog
from utils import get_addon, log, log_always, get_video_file

CHECK_INTERVAL = 1.0

def update_keymap_file():
    """Update the keymap file in userdata/keymaps based on the shortcut key setting"""
    try:
        addon = get_addon()
        shortcut_key = addon.getSetting("editor_shortcut_key").strip().lower()
        
        if not shortcut_key or len(shortcut_key) != 1:
            log("⚠️ Invalid shortcut key setting, using default 'e'")
            shortcut_key = "e"
        
        # Get userdata path
        try:
            # Try new API first (Kodi 19+)
            import xbmcvfs
            userdata_path = xbmcvfs.translatePath("special://userdata")
        except:
            try:
                # Fallback to old API (Kodi 18 and earlier)
                userdata_path = xbmc.translatePath("special://userdata")
            except:
                log("❌ Could not get userdata path")
                return False
        
        keymaps_dir = os.path.join(userdata_path, "keymaps")
        keymap_file = os.path.join(keymaps_dir, "keymap.xml")
        
        # Create keymaps directory if it doesn't exist
        if not xbmcvfs.exists(keymaps_dir):
            try:
                xbmcvfs.mkdirs(keymaps_dir)
                log(f"📁 Created keymaps directory: {keymaps_dir}")
            except Exception as mkdir_err:
                log(f"⚠️ Could not create keymaps directory: {mkdir_err}")
                return False
        
        # Read existing keymap if it exists
        existing_content = ""
        if xbmcvfs.exists(keymap_file):
            try:
                f = xbmcvfs.File(keymap_file, 'r')
                content_bytes = f.read()
                f.close()
                if isinstance(content_bytes, bytes):
                    existing_content = content_bytes.decode('utf-8')
                else:
                    existing_content = content_bytes
                log(f"📖 Read existing keymap file: {keymap_file}")
            except Exception as read_err:
                log(f"⚠️ Could not read existing keymap: {read_err}")
        
        # Generate our keymap entry (without trailing newline - we'll add it when inserting)
        # Use default.py which creates a trigger file to signal the background service
        # Always use CTRL modifier to avoid conflicts with Kodi's default keybindings
        our_entry = f'      <{shortcut_key} mod="ctrl">RunScript(service.segmenteditor)</{shortcut_key}>'
        
        # Check if our entry already exists with the correct key in both sections
        has_global = f'<{shortcut_key} mod="ctrl">RunScript(service.segmenteditor)</{shortcut_key}>' in existing_content and '<global>' in existing_content
        has_fullscreen = f'<{shortcut_key} mod="ctrl">RunScript(service.segmenteditor)</{shortcut_key}>' in existing_content and '<FullscreenVideo>' in existing_content
        has_videoosd = f'<{shortcut_key} mod="ctrl">RunScript(service.segmenteditor)</{shortcut_key}>' in existing_content and '<VideoOSD>' in existing_content
        
        if has_fullscreen and has_videoosd:
            log(f"✅ Keymap already has correct entry for key '{shortcut_key}' (CTRL+{shortcut_key}) in both sections")
            # Still add Global section if missing (optional but recommended)
            if not has_global:
                log(f"ℹ️ Adding Global section for broader compatibility")
            else:
                return True
        
        # Remove ALL old entries for our addon from both sections
        import re
        # Remove any existing entries for our addon (match any indentation and any key)
        # This regex matches: optional whitespace, <any single letter>, our script, </any single letter>, optional whitespace and newline
        lines = existing_content.split('\n')
        filtered_lines = []
        for line in lines:
            # Check if this line contains our addon script but is not the correct key
            # Match RunScript(service.segmenteditor) with or without trigger.py parameter
            if 'RunScript(service.segmenteditor' in line:
                # Check if it's the correct key with CTRL modifier
                if f'<{shortcut_key} mod="ctrl">' in line and f'</{shortcut_key}>' in line:
                    # Keep it if it's the correct key with CTRL modifier
                    filtered_lines.append(line)
                else:
                    # Skip it - it's an old entry with wrong key or missing CTRL modifier
                    log(f"🧹 Removing old entry: {line.strip()}")
            else:
                # Keep all other lines
                filtered_lines.append(line)
        
        existing_content = '\n'.join(filtered_lines)
        
        # Process Global section (optional but recommended for broader compatibility)
        global_section_match = re.search(r'<global>(.*?)</global>', existing_content, re.DOTALL)
        if global_section_match:
            global_content = global_section_match.group(1)
            # Check if our entry already exists
            if f'<{shortcut_key} mod="ctrl">RunScript(service.segmenteditor)</{shortcut_key}>' not in global_content:
                # Check if keyboard section exists in Global
                if '<keyboard>' in global_content:
                    keyboard_match = re.search(r'<keyboard>(.*?)</keyboard>', global_content, re.DOTALL)
                    if keyboard_match:
                        keyboard_inner = keyboard_match.group(1)
                        # Clean up extra whitespace/newlines and add our entry
                        keyboard_inner_clean = re.sub(r'\n\s*\n+', '\n', keyboard_inner.strip())
                        if keyboard_inner_clean:
                            new_keyboard_content = keyboard_inner_clean + '\n' + our_entry
                        else:
                            new_keyboard_content = our_entry
                        global_content = re.sub(
                            r'<keyboard>.*?</keyboard>',
                            '<keyboard>\n' + new_keyboard_content + '\n    </keyboard>',
                            global_content,
                            flags=re.DOTALL,
                            count=1
                        )
                    existing_content = re.sub(
                        r'(<global>).*?(</global>)',
                        r'\1' + global_content + r'\2',
                        existing_content,
                        flags=re.DOTALL,
                        count=1
                    )
                    log(f"✅ Added entry to Global section")
                else:
                    # Add keyboard section to Global
                    existing_content = re.sub(
                        r'(<global>)',
                        r'\1\n    <keyboard>\n' + our_entry + '\n    </keyboard>',
                        existing_content,
                        count=1
                    )
                    log(f"✅ Added keyboard section to Global")
        else:
            # Add Global section (optional, but recommended)
            if '</keymap>' in existing_content:
                existing_content = existing_content.replace(
                    '</keymap>',
                    f'  <global>\n    <keyboard>\n{our_entry}\n    </keyboard>\n  </global>\n</keymap>',
                    1
                )
            log(f"✅ Added Global section")
        
        # Process FullscreenVideo section
        fullscreen_section_match = re.search(r'<FullscreenVideo>(.*?)</FullscreenVideo>', existing_content, re.DOTALL)
        if fullscreen_section_match:
            fullscreen_content = fullscreen_section_match.group(1)
            # Check if our entry already exists
            if f'<{shortcut_key} mod="ctrl">RunScript(service.segmenteditor)</{shortcut_key}>' in fullscreen_content:
                log(f"✅ FullscreenVideo already has correct entry")
            else:
                # Check if keyboard section exists in FullscreenVideo
                if '<keyboard>' in fullscreen_content:
                    # Add our entry after <keyboard> tag (only if not already there)
                    keyboard_match = re.search(r'<keyboard>(.*?)</keyboard>', fullscreen_content, re.DOTALL)
                    if keyboard_match:
                        keyboard_inner = keyboard_match.group(1)
                        # Check if our entry already exists
                        if f'<{shortcut_key} mod="ctrl">RunScript(service.segmenteditor)</{shortcut_key}>' not in keyboard_inner:
                            # Clean up extra whitespace/newlines and add our entry
                            # Remove multiple consecutive newlines and normalize
                            keyboard_inner_clean = re.sub(r'\n\s*\n+', '\n', keyboard_inner.strip())
                            # Add our entry with proper formatting
                            if keyboard_inner_clean:
                                new_keyboard_content = keyboard_inner_clean + '\n' + our_entry
                            else:
                                new_keyboard_content = our_entry
                            # Replace with clean formatting
                            fullscreen_content = re.sub(
                                r'<keyboard>.*?</keyboard>',
                                '<keyboard>\n' + new_keyboard_content + '\n    </keyboard>',
                                fullscreen_content,
                                flags=re.DOTALL,
                                count=1
                            )
                    # Replace the section in the main content
                    existing_content = re.sub(
                        r'(<FullscreenVideo>).*?(</FullscreenVideo>)',
                        r'\1' + fullscreen_content + r'\2',
                        existing_content,
                        flags=re.DOTALL,
                        count=1
                    )
                    log(f"✅ Added entry to FullscreenVideo section")
                else:
                    # Add keyboard section to FullscreenVideo
                    existing_content = re.sub(
                        r'(<FullscreenVideo>)',
                        r'\1\n    <keyboard>\n' + our_entry + '\n    </keyboard>',
                        existing_content,
                        count=1
                    )
                    log(f"✅ Added keyboard section to FullscreenVideo")
        else:
            # Need to add FullscreenVideo section
            if '</keymap>' in existing_content:
                existing_content = existing_content.replace(
                    '</keymap>',
                    f'  <FullscreenVideo>\n    <keyboard>\n{our_entry}\n    </keyboard>\n  </FullscreenVideo>\n</keymap>'
                )
            else:
                # No keymap structure at all - create complete structure
                # Include Global section for broader compatibility, plus FullscreenVideo and VideoOSD
                existing_content = f'<?xml version="1.0" encoding="UTF-8"?>\n<keymap>\n  <global>\n    <keyboard>\n{our_entry}\n    </keyboard>\n  </global>\n  <FullscreenVideo>\n    <keyboard>\n{our_entry}\n    </keyboard>\n  </FullscreenVideo>\n  <VideoOSD>\n    <keyboard>\n{our_entry}\n    </keyboard>\n  </VideoOSD>\n</keymap>\n'
            log(f"✅ Added FullscreenVideo section")
        
        # Process VideoOSD section
        videoosd_section_match = re.search(r'<VideoOSD>(.*?)</VideoOSD>', existing_content, re.DOTALL)
        if videoosd_section_match:
            videoosd_content = videoosd_section_match.group(1)
            # Check if our entry already exists
            if f'<{shortcut_key} mod="ctrl">RunScript(service.segmenteditor)</{shortcut_key}>' in videoosd_content:
                log(f"✅ VideoOSD already has correct entry")
            else:
                # Check if keyboard section exists in VideoOSD
                if '<keyboard>' in videoosd_content:
                    # Add our entry after <keyboard> tag (only if not already there)
                    keyboard_match = re.search(r'<keyboard>(.*?)</keyboard>', videoosd_content, re.DOTALL)
                    if keyboard_match:
                        keyboard_inner = keyboard_match.group(1)
                        # Check if our entry already exists
                        if f'<{shortcut_key} mod="ctrl">RunScript(service.segmenteditor)</{shortcut_key}>' not in keyboard_inner:
                            # Clean up extra whitespace/newlines and add our entry
                            # Remove multiple consecutive newlines and normalize
                            keyboard_inner_clean = re.sub(r'\n\s*\n+', '\n', keyboard_inner.strip())
                            # Add our entry with proper formatting
                            if keyboard_inner_clean:
                                new_keyboard_content = keyboard_inner_clean + '\n' + our_entry
                            else:
                                new_keyboard_content = our_entry
                            # Replace with clean formatting
                            videoosd_content = re.sub(
                                r'<keyboard>.*?</keyboard>',
                                '<keyboard>\n' + new_keyboard_content + '\n    </keyboard>',
                                videoosd_content,
                                flags=re.DOTALL,
                                count=1
                            )
                    # Replace the section in the main content
                    existing_content = re.sub(
                        r'(<VideoOSD>).*?(</VideoOSD>)',
                        r'\1' + videoosd_content + r'\2',
                        existing_content,
                        flags=re.DOTALL,
                        count=1
                    )
                    log(f"✅ Added entry to VideoOSD section")
                else:
                    # Add keyboard section to VideoOSD
                    existing_content = re.sub(
                        r'(<VideoOSD>)',
                        r'\1\n    <keyboard>\n' + our_entry + '\n    </keyboard>',
                        existing_content,
                        count=1
                    )
                    log(f"✅ Added keyboard section to VideoOSD")
        else:
            # Need to add VideoOSD section
            if '</keymap>' in existing_content:
                existing_content = existing_content.replace(
                    '</keymap>',
                    f'  <VideoOSD>\n    <keyboard>\n{our_entry}\n    </keyboard>\n  </VideoOSD>\n</keymap>'
                )
            log(f"✅ Added VideoOSD section")
        
        # Write the updated keymap
        try:
            f = xbmcvfs.File(keymap_file, 'w')
            if f:
                result = f.write(existing_content.encode('utf-8'))
                f.close()
                if result:
                    log(f"✅ Updated keymap file with key '{shortcut_key}': {keymap_file}")
                    return True
                else:
                    log(f"⚠️ Write returned no bytes for keymap file")
                    return False
            else:
                log(f"❌ Could not open keymap file for writing")
                return False
        except Exception as write_err:
            log(f"❌ Could not write keymap file: {write_err}")
            return False
            
    except Exception as e:
        log(f"❌ Error updating keymap file: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        return False

class PlaybackMonitor(xbmc.Monitor):
    def __init__(self):
        super().__init__()
        self.last_video = None
        self.editor_open = False
        self.last_shortcut_key = None
    
    def onSettingsChanged(self):
        """Handle settings changes"""
        try:
            addon = get_addon()
            current_key = addon.getSetting("editor_shortcut_key").strip().lower()
            if current_key != self.last_shortcut_key:
                log_always(f"🔧 Shortcut key setting changed to '{current_key}'")
                self.last_shortcut_key = current_key
                update_keymap_file()
        except Exception as e:
            log(f"⚠️ Error handling settings change: {e}")
    
    def onNotification(self, sender, method, data):
        """Handle notifications from other addons or scripts"""
        log_always(f"🔔 Notification received: sender={sender}, method={method}, data={data}")
        if method == "Other.open_segment_editor" or "open_segment_editor" in str(data).lower():
            log_always("🔔 Open editor notification detected")
            open_segment_editor()

monitor = PlaybackMonitor()
player = xbmc.Player()

def open_segment_editor(video_path=None):
    """Open the segment editor dialog for the current or specified video"""
    log_always("📝 open_segment_editor() called")
    
    if monitor.editor_open:
        log_always("⚠️ Editor already open, ignoring request")
        return
    
    if not video_path:
        log_always("🔍 Getting video file...")
        video_path = get_video_file()
    
    if not video_path:
        log_always("❌ No video file available for editing")
        xbmcgui.Dialog().ok("Segment Editor", "No video is currently playing.")
        return
    
    log_always(f"📝 Opening segment editor for: {os.path.basename(video_path)}")
    monitor.editor_open = True
    
    try:
        # Try to load existing segments
        segments = parse_chapters(video_path)
        if not segments:
            segments = parse_edl(video_path)
        
        # Get current playback time if available
        current_time = None
        try:
            if player.isPlayingVideo():
                current_time = player.getTime()
        except:
            pass
        
        # Create and show editor dialog
        addon = get_addon()
        log_always("🎨 Creating SegmentEditorDialog...")
        try:
            dialog = SegmentEditorDialog(
                "SegmentEditorDialog.xml",
                addon.getAddonInfo("path"),
                "default",
                video_path=video_path,
                segments=segments or [],
                current_time=current_time
            )
            log_always("✅ Dialog created, calling doModal()...")
            dialog.doModal()
            log_always("✅ doModal() completed")
        except Exception as dialog_err:
            log_always(f"❌ Error creating/showing dialog: {dialog_err}")
            import traceback
            log_always(f"Traceback: {traceback.format_exc()}")
            raise  # Re-raise to be caught by outer try/except
        
        # Check if segments were modified
        if dialog.segments_modified:
            log("💾 Segments were modified, saving...")
            addon = get_addon()
            save_format = addon.getSetting("save_format")
            
            if dialog.segments:
                # Determine what to save based on setting
                if save_format == "both":
                    # Save to both formats
                    save_edl(video_path, dialog.segments)
                    save_chapters(video_path, dialog.segments)
                    log("💾 Saved to both EDL and XML formats")
                elif save_format == "xml":
                    # Save to XML only
                    save_chapters(video_path, dialog.segments)
                    log("💾 Saved to XML format")
                elif save_format == "edl":
                    # Save to EDL only
                    save_edl(video_path, dialog.segments)
                    log("💾 Saved to EDL format")
                else:
                    # Auto detect - use existing format or default to EDL
                    if dialog.segments[0].source == "xml":
                        save_chapters(video_path, dialog.segments)
                    else:
                        save_edl(video_path, dialog.segments)
                    log("💾 Saved using auto-detected format")
            else:
                # No segments left, delete files based on save format
                base = os.path.splitext(video_path)[0]
                files_to_delete = []
                
                if save_format == "both":
                    files_to_delete = [
                        f"{base}-chapters.xml",
                        f"{base}_chapters.xml",
                        f"{base}.edl"
                    ]
                elif save_format == "xml":
                    files_to_delete = [
                        f"{base}-chapters.xml",
                        f"{base}_chapters.xml"
                    ]
                elif save_format == "edl":
                    files_to_delete = [f"{base}.edl"]
                else:
                    # Auto detect - delete all possible files
                    files_to_delete = [
                        f"{base}-chapters.xml",
                        f"{base}_chapters.xml",
                        f"{base}.edl"
                    ]
                
                for path in files_to_delete:
                    if xbmcvfs.exists(path):
                        try:
                            xbmcvfs.delete(path)
                            log(f"🗑️ Deleted empty segment file: {path}")
                        except:
                            pass
            
            xbmcgui.Dialog().notification(
                "Segment Editor",
                "Segments saved successfully",
                time=2000
            )
        
        del dialog
    except Exception as e:
        log(f"❌ Error opening editor: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        xbmcgui.Dialog().ok("Segment Editor", f"Error opening editor: {str(e)}")
    finally:
        monitor.editor_open = False

# Wrap entire service startup in try/except to catch any errors
try:
    log_always("📡 Segment Editor service started")
    log_always("💡 To open the editor during playback, use the context menu or install keymap.xml")

    # Create a trigger file path for external triggering
    addon = get_addon()
    if not addon:
        log_always("❌ CRITICAL: Could not get addon object!")
    else:
        addon_path = addon.getAddonInfo('path')
        trigger_file = os.path.join(addon_path, "trigger_editor.txt")
        log_always(f"📂 Trigger file path: {trigger_file}")
        
        # Update keymap file based on settings
        try:
            shortcut_key = addon.getSetting("editor_shortcut_key").strip().lower()
            monitor.last_shortcut_key = shortcut_key if shortcut_key else "e"
            log_always(f"⌨️ Keyboard shortcut key: '{monitor.last_shortcut_key}'")
            if update_keymap_file():
                log_always("✅ Keymap file updated successfully")
            else:
                log_always("⚠️ Keymap file update failed - you may need to manually edit keymap.xml")
        except Exception as keymap_err:
            log_always(f"⚠️ Error updating keymap: {keymap_err}")

        while not monitor.abortRequested():
            # Check if video is playing
            if player.isPlayingVideo():
                video = get_video_file()
                
                if video and video != monitor.last_video:
                    log(f"🎬 New video detected: {os.path.basename(video)}")
                    monitor.last_video = video
            
            # Check for trigger file (alternative method to open editor)
            # Check this regardless of whether video is playing
            try:
                if xbmcvfs.exists(trigger_file):
                    log_always("🔔 Trigger file detected")
                    
                    # Check if editor is already open FIRST (before deleting file)
                    if monitor.editor_open:
                        log_always("⚠️ Editor already open, deleting trigger file and ignoring")
                        try:
                            xbmcvfs.delete(trigger_file)
                        except:
                            pass
                    else:
                        # Delete trigger file IMMEDIATELY to prevent other service instances from detecting it
                        try:
                            xbmcvfs.delete(trigger_file)
                            log_always("🗑️ Trigger file deleted immediately to prevent multiple instances")
                        except Exception as del_err:
                            log_always(f"⚠️ Error deleting trigger file: {del_err}")
                        
                        # Small delay to ensure file deletion is processed
                        time.sleep(0.1)
                        
                        # Double-check editor is still not open (race condition protection)
                        if not monitor.editor_open:
                            # Try to open editor
                            try:
                                open_segment_editor()
                                log_always("✅ open_segment_editor() completed successfully")
                            except Exception as open_err:
                                log_always(f"❌ Error calling open_segment_editor(): {open_err}")
                                import traceback
                                log_always(f"Traceback: {traceback.format_exc()}")
                        else:
                            log_always("⚠️ Editor opened by another instance, skipping")
            except Exception as e:
                log_always(f"⚠️ Error checking trigger file: {e}")
                import traceback
                log_always(f"Traceback: {traceback.format_exc()}")
            
            # Wait for abort or interval
            if monitor.waitForAbort(CHECK_INTERVAL):
                log_always("🛑 Abort requested — exiting monitor loop")
                break
except Exception as critical_err:
    # Last resort error handling - use direct xbmc.log in case get_addon() fails
    try:
        xbmc.log(f"[service.segmenteditor] ❌❌❌ CRITICAL SERVICE STARTUP ERROR: {critical_err}", xbmc.LOGERROR)
        import traceback
        xbmc.log(f"[service.segmenteditor] Traceback: {traceback.format_exc()}", xbmc.LOGERROR)
    except:
        # If even logging fails, we're in deep trouble
        pass

