import xbmcgui
import xbmc
import xbmcaddon
import time
import threading
import os

from segment_parser import SegmentItem, seconds_to_hms, hms_to_seconds, save_edl, save_chapters
from utils import get_addon, log, log_always

class SegmentEditorDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.video_path = kwargs.get("video_path")
        self.segments = kwargs.get("segments", [])
        self.current_time = kwargs.get("current_time", 0)
        self.segments_modified = False
        self.selected_index = -1
        self.player = xbmc.Player()
        self._closing = False
        self.pending_start_time = None
        self.pending_end_time = None
        self.is_paused = False
        self._explicit_click = False  # Flag to track explicit clicks vs focus changes
        self._previous_focus = None  # Track previous focus to detect navigation source
        
        # Get addon icon path for notifications
        try:
            addon = get_addon()
            addon_path = addon.getAddonInfo('path')
            self.icon_path = os.path.join(addon_path, "icon.png")
        except:
            self.icon_path = None
        
        log(f"📦 SegmentEditorDialog initialized with {len(self.segments)} segments")
    
    def onInit(self):
        """Initialize the dialog"""
        try:
            log_always("🔍 onInit called")
            
            # Check if full-screen overlay should be enabled
            try:
                addon = get_addon()
                enable_overlay = addon.getSetting("enable_fullscreen_overlay") == "true"
                # Control ID for the full-screen overlay is not explicitly set, so we need to find it
                # The overlay is the first image control in the window
                # We'll use a property to control visibility via XML, or directly hide it
                # Since we can't easily reference it by ID, we'll use window property
                self.setProperty("EnableFullscreenOverlay", "true" if enable_overlay else "false")
                log(f"🔍 Full-screen overlay setting: {enable_overlay}")
            except Exception as e:
                log(f"⚠️ Error reading overlay setting: {e}")
                # Default to disabled
                self.setProperty("EnableFullscreenOverlay", "false")
            
            # Set up list control
            self.list_control = self.getControl(5000)
            if not self.list_control:
                log_always("❌ List control (5000) not found - this is critical!")
                # Still try to continue, but log the error
            else:
                # Populate list
                self.refresh_list()
                # Update button positions after list is set up
                self.update_button_positions()
            
            # Initialize pause button - detect actual player state
            try:
                self.is_paused = self._detect_pause_state()
                pause_button = self.getControl(5018)
                if pause_button:
                    # Set button label: "Pause" when playing (not paused), "Resume" when paused
                    pause_button.setLabel("Pause" if not self.is_paused else "Resume")
                    log(f"🔍 Initial pause state detected: {self.is_paused} (button shows: {pause_button.getLabel()})")
            except Exception as e:
                log(f"⚠️ Error initializing pause button: {e}")
                # Default to not paused if detection fails
                self.is_paused = False
            
            # Set initial focus to Pause/Resume button
            try:
                self.setFocusId(5018)
                log_always("✅ Set initial focus to Pause/Resume button (5018)")
            except:
                log_always("⚠️ Could not set initial focus to Pause/Resume button")
            
            # Make sure all buttons are visible and enabled
            try:
                button_ids = [5002, 5003, 5004, 5005, 5006, 5007, 5009, 5010, 5011, 5012, 5013, 5014, 5015, 5016, 5017, 5018, 5019, 5020, 5021, 5022, 5023, 5024, 5025]
                for btn_id in button_ids:
                    try:
                        btn = self.getControl(btn_id)
                        if btn:
                            btn.setEnabled(True)
                            btn.setVisible(True)
                    except:
                        pass
                # Update Edit/Delete button positions after all buttons are initialized
                self.update_button_positions()
            except:
                pass
            
            # Start time update thread
            threading.Thread(target=self._update_time_display, daemon=True).start()
            
            log("✅ Dialog onInit completed")
        except Exception as e:
            log_always(f"❌ Error in onInit: {e}")
            import traceback
            log_always(f"Traceback: {traceback.format_exc()}")
    
    def _detect_pause_state(self):
        """Detect if the player is currently paused by sampling playback time"""
        try:
            if not self.player.isPlayingVideo():
                return False  # Not playing, so not paused
            
            # Get initial time
            time1 = self.player.getTime()
            # Wait a short moment
            time.sleep(0.15)
            # Get time again
            time2 = self.player.getTime()
            
            # If time hasn't changed (or changed very little due to rounding), it's paused
            # Allow for small differences (0.05 seconds) due to timing precision
            time_difference = abs(time2 - time1)
            is_paused = time_difference < 0.05
            
            log(f"🔍 Pause detection: time1={time1:.3f}, time2={time2:.3f}, diff={time_difference:.3f}, paused={is_paused}")
            return is_paused
        except Exception as e:
            log(f"⚠️ Error detecting pause state: {e}")
            return False  # Default to not paused if detection fails
    
    def _update_time_display(self):
        """Update the current time display in real-time"""
        last_time = None
        consecutive_stable_samples = 0
        while not self._closing:
            try:
                if self.player.isPlayingVideo():
                    current = self.player.getTime()
                    
                    # Detect pause state by comparing consecutive time values
                    # Need multiple consecutive stable samples to avoid false positives
                    if last_time is not None:
                        time_diff = abs(current - last_time)
                        # If time difference is very small (< 0.15 seconds for 0.5s interval = 30% of expected),
                        # likely paused (accounting for rounding and system delays)
                        # Update interval is 0.5s, so normal playback should advance ~0.5s per update
                        if time_diff < 0.15:
                            consecutive_stable_samples += 1
                            # After 2 consecutive samples with minimal time change, consider it paused
                            if consecutive_stable_samples >= 2:
                                if not self.is_paused:
                                    log(f"🔍 Detected pause state change: playing -> paused (time stable for {consecutive_stable_samples} samples, diff={time_diff:.3f}s)")
                                    self.is_paused = True
                                    # Update button label
                                    try:
                                        pause_button = self.getControl(5018)
                                        if pause_button:
                                            pause_button.setLabel("Resume")
                                    except:
                                        pass
                        else:
                            # Time is advancing significantly, so not paused
                            consecutive_stable_samples = 0
                            if self.is_paused:
                                log(f"🔍 Detected pause state change: paused -> playing (time advancing: {time_diff:.3f}s)")
                                self.is_paused = False
                                # Update button label
                                try:
                                    pause_button = self.getControl(5018)
                                    if pause_button:
                                        pause_button.setLabel("Pause")
                                except:
                                    pass
                    else:
                        consecutive_stable_samples = 0
                    
                    last_time = current
                    self.current_time = current
                    hms = seconds_to_hms(current)
                    
                    # Update the time label
                    try:
                        time_label = self.getControl(5001)
                        if time_label:
                            # Show [PAUSED] when actually paused (is_paused = True)
                            pause_indicator = " [PAUSED]" if self.is_paused else ""
                            time_label.setLabel(f"Current Time: {hms}{pause_indicator}")
                    except:
                        pass
                    
                    # Show pending start/end markers
                    status_text = ""
                    if self.pending_start_time is not None:
                        status_text = f"Start: {seconds_to_hms(self.pending_start_time)}"
                    if self.pending_end_time is not None:
                        if status_text:
                            status_text += f" | End: {seconds_to_hms(self.pending_end_time)}"
                        else:
                            status_text = f"End: {seconds_to_hms(self.pending_end_time)}"
                    
                    # Add validation warning if times are invalid
                    if self.pending_start_time is not None and self.pending_end_time is not None:
                        if self.pending_end_time <= self.pending_start_time:
                            status_text += " [INVALID: End must be after Start]"
                    
                    try:
                        status_label = self.getControl(5008)
                        if status_label:
                            status_label.setLabel(status_text)
                    except:
                        pass
            except:
                pass
            
            time.sleep(0.5)  # Update twice per second
    
    def refresh_list(self):
        """Refresh the segments list"""
        try:
            if not hasattr(self, 'list_control') or not self.list_control:
                log("⚠️ List control not available, skipping refresh")
                return
            
            items = []
            # Check for nested segments (fully contained)
            nested_indices = set()
            for i, seg in enumerate(self.segments):
                for j, other_seg in enumerate(self.segments):
                    if i != j:
                        # Check if seg is nested inside other_seg
                        if (other_seg.start_seconds <= seg.start_seconds and 
                            seg.end_seconds <= other_seg.end_seconds):
                            nested_indices.add(i)
                            break
            
            # Check for overlapping segments (partially overlapping but not fully nested)
            overlapping_indices = set()
            for i, seg in enumerate(self.segments):
                if i in nested_indices:
                    continue  # Skip if already marked as nested
                for j, other_seg in enumerate(self.segments):
                    if i != j and j not in nested_indices:
                        # Check if segments overlap (but neither is fully nested)
                        # Two segments overlap if: seg1.start < seg2.end AND seg2.start < seg1.end
                        if (seg.start_seconds < other_seg.end_seconds and 
                            other_seg.start_seconds < seg.end_seconds):
                            # Make sure neither is fully nested
                            seg_nested_in_other = (other_seg.start_seconds <= seg.start_seconds and 
                                                   seg.end_seconds <= other_seg.end_seconds)
                            other_nested_in_seg = (seg.start_seconds <= other_seg.start_seconds and 
                                                   other_seg.end_seconds <= seg.end_seconds)
                            if not seg_nested_in_other and not other_nested_in_seg:
                                overlapping_indices.add(i)
                            break
            
            for i, seg in enumerate(self.segments):
                # Format time display
                start_hms = seconds_to_hms(seg.start_seconds)
                end_hms = seconds_to_hms(seg.end_seconds)
                duration = seg.get_duration()
                
                label = f"{seg.raw_label if hasattr(seg, 'raw_label') else seg.segment_type_label}"
                # Number segments starting from 1, capitalize "Segment"
                segment_num = i + 1
                is_nested = i in nested_indices
                is_overlapping = i in overlapping_indices
                # Format line1 - XML will handle the nested/overlapping indicator
                line1 = f"Segment {segment_num} - {label} - {start_hms} to {end_hms}"
                line2 = f"Duration: {duration:.1f}s | Source: {seg.source}"
                
                item = xbmcgui.ListItem(line1, line2)
                item.setProperty("index", str(i))
                item.setProperty("start", str(seg.start_seconds))
                item.setProperty("end", str(seg.end_seconds))
                item.setProperty("label", label)
                item.setProperty("is_nested", "true" if is_nested else "false")
                item.setProperty("is_overlapping", "true" if is_overlapping else "false")
                # Combined property for easier visibility checking: "normal", "nested", or "overlapping"
                if is_nested:
                    item.setProperty("segment_type", "nested")
                elif is_overlapping:
                    item.setProperty("segment_type", "overlapping")
                else:
                    item.setProperty("segment_type", "normal")
                item.setProperty("segment_num", str(segment_num))
                item.setProperty("start_hms", start_hms)
                item.setProperty("end_hms", end_hms)
                items.append(item)
            
            self.list_control.reset()
            self.list_control.addItems(items)
            
            # Show/hide Edit and Delete buttons based on whether there are segments
            # Also set HasSegments property for new buttons visibility
            try:
                has_segments = len(self.segments) > 0
                self.setProperty("HasSegments", "true" if has_segments else "false")
                
                edit_btn = self.getControl(5021)
                delete_btn = self.getControl(5022)
                if edit_btn:
                    edit_btn.setVisible(has_segments)
                if delete_btn:
                    delete_btn.setVisible(has_segments)
            except:
                pass
            
            if items:
                self.list_control.selectItem(0)
                self.selected_index = 0
                # Update button positions after refresh
                self.update_button_positions()
            
            log(f"✅ List refreshed with {len(items)} items")
        except Exception as e:
            log(f"❌ Error refreshing list: {e}")
    
    def onClick(self, controlId):
        """Handle button clicks - only called on explicit Select/Enter press"""
        log(f"🖱️ onClick called with controlId: {controlId}, explicit_click={self._explicit_click}")
        
        # Only process clicks if this was an explicit click, not a focus change
        if not self._explicit_click:
            log("⚠️ onClick called but not an explicit click - ignoring")
            return
        
        # Reset the flag
        self._explicit_click = False
        
        # Ensure we have a valid player reference
        try:
            if not self.player.isPlayingVideo():
                log("⚠️ Video is not playing, some actions may not work")
        except:
            log("⚠️ Could not check player state")
        
        # Only process clicks for buttons that should activate
        if controlId == 5002:  # Add button
            log("➕ Add button clicked")
            self.add_segment()
        elif controlId == 5004:  # Delete All button
            log("🗑️ Delete All button clicked")
            self.delete_all_segments()
        elif controlId == 5005:  # Add at current time
            log("⏰ Add at current time button clicked")
            self.add_at_current_time()
        elif controlId == 5006:  # Save
            log("💾 Save button clicked")
            self.save_segments()
        elif controlId == 5007:  # Exit
            log("❌ Exit button clicked")
            if self.check_unsaved_changes():
                self._closing = True
                self.close()
        elif controlId == 5009:  # Seek back 5s
            log("⏪ Seek -5s button clicked")
            self.seek_relative(-5)
        elif controlId == 5010:  # Seek back 10s
            log("⏪ Seek -10s button clicked")
            self.seek_relative(-10)
        elif controlId == 5011:  # Seek back 30s
            log("⏪ Seek -30s button clicked")
            self.seek_relative(-30)
        elif controlId == 5012:  # Seek forward 5s
            log("⏩ Seek +5s button clicked")
            self.seek_relative(5)
        elif controlId == 5013:  # Seek forward 10s
            log("⏩ Seek +10s button clicked")
            self.seek_relative(10)
        elif controlId == 5014:  # Seek forward 30s
            log("⏩ Seek +30s button clicked")
            self.seek_relative(30)
        elif controlId == 5019:  # Seek back 1s
            log("⏪ Seek -1s button clicked")
            self.seek_relative(-1)
        elif controlId == 5020:  # Seek forward 1s
            log("⏩ Seek +1s button clicked")
            self.seek_relative(1)
        elif controlId == 5015:  # Set as Start
            log("📍 Set as Start button clicked")
            self.set_as_start()
        elif controlId == 5016:  # Set as End
            log("📍 Set as End button clicked")
            self.set_as_end()
        elif controlId == 5017:  # Add with marked times
            log("➕ Add with marked times button clicked")
            self.add_with_marked_times()
        elif controlId == 5023:  # Start at End of
            log("📍 Start at End of segment button clicked")
            self.start_at_end_of_segment()
        elif controlId == 5024:  # End at Start of
            log("📍 End at Start of segment button clicked")
            self.end_at_start_of_segment()
        elif controlId == 5018:  # Pause/Play toggle
            log("⏸️ Pause/Play button clicked")
            self.toggle_pause()
        elif controlId == 5025:  # Jump To
            log("⏩ Jump To button clicked")
            self.jump_to_time()
        elif controlId == 5021:  # Edit button in list item
            log("✏️ Edit button in list item clicked")
            self.edit_segment()
        elif controlId == 5022:  # Delete button in list item
            log("🗑️ Delete button in list item clicked")
            self.delete_segment()
        else:
            log(f"⚠️ Unknown controlId clicked: {controlId}")
    
    def onAction(self, action):
        """Handle actions"""
        action_id = action.getId()
        focused = self.getFocusId()
        log(f"🎮 onAction: action_id={action_id}, focus={focused}")
        
        # ESC or Back button
        if action_id in [10, 92]:
            log("🔙 ESC/Back pressed")
            if self.check_unsaved_changes():
                self.close()
            return
        
        # Enter/Select - handle for both list and buttons
        # Only activate buttons when Select is explicitly pressed, not on focus
        if action_id == 7:  # Select
            log(f"✅ Select action, focused control: {focused}")
            if focused == 5000:
                # List item selected - update selected index and jump to segment start
                self.update_button_positions()  # Ensure selected_index is up to date
                self.jump_to_segment_start()
                return  # Don't process further
            # For buttons, only activate on explicit Select press
            elif focused in [5009, 5010, 5011, 5012, 5013, 5014, 5015, 5016, 5017, 5018, 5019, 5020, 5002, 5004, 5005, 5006, 5007, 5021, 5022, 5023, 5024, 5025]:
                # Set flag to indicate this is an explicit click
                self._explicit_click = True
                # Trigger onClick for the focused button
                log(f"🖱️ Triggering onClick for button {focused} (explicit click)")
                self.onClick(focused)
            return  # Don't process other actions when Select is pressed
        
        # Keyboard shortcuts for quick access - ONLY when list is focused
        # Left/Right arrow keys should NOT seek - user should use seek buttons below
        # We'll let XML handle navigation for Left/Right arrows
        if action_id == 1:  # Left
            # Don't seek - let XML handle navigation
            return
        elif action_id == 2:  # Right
            # Don't seek - let XML handle navigation
            return
        
        # Space for pause/play - only when list is focused
        if action_id == 11:  # Space
            if focused == 5000:  # Only pause when list is focused
                log("⏸️ Space pressed - toggling pause")
                self.toggle_pause()
            return
        
        # S key for "Set as Start" - only when list is focused
        if action_id in [115, 83, 19]:  # 's', 'S', or alternative
            if focused == 5000:  # Only when list is focused
                log("📍 S key pressed - setting as start")
                self.set_as_start()
            return
        
        # E key for "Set as End" - only when list is focused
        if action_id in [101, 69, 18]:  # 'e', 'E', or alternative
            if focused == 5000:  # Only when list is focused
                log("📍 E key pressed - setting as end")
                self.set_as_end()
            return
        
        # D key for "Delete" - only when list is focused
        if action_id in [100, 68, 20]:  # 'd', 'D', or alternative
            if focused == 5000:
                log("🗑️ D key pressed - deleting segment")
                self.delete_segment()
            return
        
        # Handle list navigation to update button positions
        if action_id in [3, 4]:  # Up (3) or Down (4) arrow
            if focused == 5000:  # List is focused
                # Small delay to let list selection update, then update button positions
                import threading
                def update_after_nav():
                    import time
                    time.sleep(0.05)  # Small delay
                    self.update_button_positions()
                threading.Thread(target=update_after_nav, daemon=True).start()
        
        # Don't intercept other navigation - let XML handle it
        # The XML onup/ondown properties should handle navigation between list and buttons
    
    def add_at_current_time(self):
        """Add a new segment starting at current playback time"""
        if not self.current_time or self.current_time <= 0:
            xbmcgui.Dialog().ok("Segment Editor", "No current playback time available.")
            return
        
        # Get duration from user
        duration_str = xbmcgui.Dialog().input(
            "Segment Duration (seconds)",
            defaultt="30"
        )
        
        if not duration_str:
            return
        
        try:
            duration = float(duration_str)
            start = self.current_time
            end = start + duration
            
            # Get label with predefined options
            label = self.get_label_from_user()
            if label is None:
                return  # User cancelled
            
            # Determine source type based on existing segments
            source = "edl"
            if self.segments and self.segments[0].source == "xml":
                source = "xml"
            
            new_seg = SegmentItem(start, end, label, source=source)
            self.segments.append(new_seg)
            self.segments.sort(key=lambda s: s.start_seconds)
            self.segments_modified = True
            self.refresh_list()
            
            log(f"✅ Added segment at current time: {new_seg}")
        except ValueError:
            xbmcgui.Dialog().ok("Segment Editor", "Invalid duration value.")
    
    def add_segment(self):
        """Add a new segment"""
        # Check if we have marked times
        if self.pending_start_time is not None and self.pending_end_time is not None:
            if xbmcgui.Dialog().yesno(
                "Segment Editor",
                "You have marked start and end times.\n\n"
                "Use 'Add with Marked Times' instead?"
            ):
                self.add_with_marked_times()
                return
        
        # Get start time (offer current time or marked time as default)
        default_start = "0"
        if self.pending_start_time is not None:
            default_start = seconds_to_hms(self.pending_start_time)
        elif self.current_time > 0:
            default_start = seconds_to_hms(self.current_time)
        
        start_str = xbmcgui.Dialog().input(
            "Start Time (HH:MM:SS.mmm or seconds)",
            defaultt=default_start
        )
        if not start_str:
            return
        
        # Get end time (offer marked time or current time + 30s as default)
        default_end = "30"
        if self.pending_end_time is not None:
            default_end = seconds_to_hms(self.pending_end_time)
        elif self.current_time > 0:
            default_end = seconds_to_hms(self.current_time + 30)
        
        end_str = xbmcgui.Dialog().input(
            "End Time (HH:MM:SS.mmm or seconds)",
            defaultt=default_end
        )
        if not end_str:
            return
        
        # Get label with predefined options
        label = self.get_label_from_user()
        if label is None:
            return  # User cancelled
        
        try:
            # Parse times
            if ":" in start_str:
                start = hms_to_seconds(start_str)
            else:
                start = float(start_str)
            
            if ":" in end_str:
                end = hms_to_seconds(end_str)
            else:
                end = float(end_str)
            
            if end <= start:
                xbmcgui.Dialog().ok("Segment Editor", "End time must be after start time.")
                return
            
            # Determine source type
            source = "edl"
            if self.segments and self.segments[0].source == "xml":
                source = "xml"
            
            new_seg = SegmentItem(start, end, label, source=source)
            self.segments.append(new_seg)
            self.segments.sort(key=lambda s: s.start_seconds)
            self.segments_modified = True
            self.refresh_list()
            
            log(f"✅ Added segment: {new_seg}")
        except (ValueError, Exception) as e:
            xbmcgui.Dialog().ok("Segment Editor", f"Invalid input: {str(e)}")
    
    def edit_segment(self):
        """Edit the selected segment"""
        if self.selected_index < 0 or self.selected_index >= len(self.segments):
            xbmcgui.Dialog().ok("Segment Editor", "Please select a segment to edit.")
            return
        
        seg = self.segments[self.selected_index]
        
        # Check if we have marked times
        if self.pending_start_time is not None and self.pending_end_time is not None:
            if xbmcgui.Dialog().yesno(
                "Segment Editor",
                "You have marked start and end times.\n\n"
                "Use marked times for this segment?"
            ):
                if self.pending_end_time > self.pending_start_time:
                    seg.start_seconds = self.pending_start_time
                    seg.end_seconds = self.pending_end_time
                    self.pending_start_time = None
                    self.pending_end_time = None
                    self.segments.sort(key=lambda s: s.start_seconds)
                    self.segments_modified = True
                    self.refresh_list()
                    log(f"✅ Edited segment with marked times: {seg}")
                    return
                else:
                    xbmcgui.Dialog().ok("Segment Editor", "End time must be after start time.")
                    return
        
        # Get new start time (offer marked time or current value as default)
        default_start = seconds_to_hms(seg.start_seconds)
        if self.pending_start_time is not None:
            default_start = seconds_to_hms(self.pending_start_time)
        
        start_str = xbmcgui.Dialog().input(
            "Start Time (HH:MM:SS.mmm or seconds)",
            defaultt=default_start
        )
        if not start_str:
            return
        
        # Get new end time (offer marked time or current value as default)
        default_end = seconds_to_hms(seg.end_seconds)
        if self.pending_end_time is not None:
            default_end = seconds_to_hms(self.pending_end_time)
        
        end_str = xbmcgui.Dialog().input(
            "End Time (HH:MM:SS.mmm or seconds)",
            defaultt=default_end
        )
        if not end_str:
            return
        
        # Get new label with predefined options
        default_label = seg.raw_label if hasattr(seg, 'raw_label') else seg.segment_type_label
        label = self.get_label_from_user(default=default_label)
        if label is None:
            return  # User cancelled
        
        try:
            # Parse times
            if ":" in start_str:
                start = hms_to_seconds(start_str)
            else:
                start = float(start_str)
            
            if ":" in end_str:
                end = hms_to_seconds(end_str)
            else:
                end = float(end_str)
            
            if end <= start:
                xbmcgui.Dialog().ok("Segment Editor", "End time must be after start time.")
                return
            
            # Update segment
            seg.start_seconds = start
            seg.end_seconds = end
            seg.raw_label = label
            seg.segment_type_label = label.lower().strip()
            self.segments.sort(key=lambda s: s.start_seconds)
            self.segments_modified = True
            self.refresh_list()
            
            log(f"✅ Edited segment: {seg}")
        except (ValueError, Exception) as e:
            xbmcgui.Dialog().ok("Segment Editor", f"Invalid input: {str(e)}")
    
    def delete_segment(self):
        """Delete the selected segment"""
        if self.selected_index < 0 or self.selected_index >= len(self.segments):
            xbmcgui.Dialog().ok("Segment Editor", "Please select a segment to delete.")
            return
        
        seg = self.segments[self.selected_index]
        label = seg.raw_label if hasattr(seg, 'raw_label') else seg.segment_type_label
        
        if xbmcgui.Dialog().yesno("Segment Editor", f"Delete segment '{label}'?"):
            del self.segments[self.selected_index]
            self.segments_modified = True
            self.refresh_list()
            # Update button positions after deletion
            self.update_button_positions()
            log(f"✅ Deleted segment: {label}")
    
    def update_button_positions(self):
        """Update Edit/Delete button positions based on selected list item"""
        try:
            if not hasattr(self, 'list_control') or not self.list_control:
                return
            
            # Get the selected index
            selected = self.list_control.getSelectedPosition()
            if selected < 0:
                selected = 0
            if selected >= len(self.segments):
                selected = len(self.segments) - 1 if self.segments else 0
            
            self.selected_index = selected
            
            # Calculate button position based on selected item
            # List starts at top=110, each item is 50px high
            # Buttons should align with the selected item (center vertically in the item)
            list_top = 110
            item_height = 50
            button_top = list_top + (selected * item_height) + 10  # +10 to center vertically in item (item is 50px, button is 30px, so 10px from top centers it)
            
            # Update button positions (only vertical position to align with selected item)
            # Horizontal positions are handled by XML
            try:
                edit_btn = self.getControl(5021)
                delete_btn = self.getControl(5022)
                has_segments = len(self.segments) > 0
                if edit_btn:
                    # Get current x position from XML and only update y position
                    current_x, _ = edit_btn.getPosition()
                    edit_btn.setPosition(current_x, button_top)
                    edit_btn.setVisible(has_segments)
                    edit_btn.setEnabled(True)
                if delete_btn:
                    # Get current x position from XML and only update y position
                    current_x, _ = delete_btn.getPosition()
                    delete_btn.setPosition(current_x, button_top)
                    delete_btn.setVisible(has_segments)
                    delete_btn.setEnabled(has_segments)
                log(f"📍 Updated button vertical positions for segment {selected + 1} (index {selected}) at top={button_top}")
            except Exception as e:
                log(f"⚠️ Error updating button positions: {e}")
                import traceback
                log(f"Traceback: {traceback.format_exc()}")
        except Exception as e:
            log(f"⚠️ Error in update_button_positions: {e}")
            import traceback
            log(f"Traceback: {traceback.format_exc()}")
    
    def onFocus(self, controlId):
        """Handle focus changes"""
        log(f"🎯 Focus changed to control: {controlId} (previous: {self._previous_focus})")
        # Reset explicit click flag when focus changes
        self._explicit_click = False
        if controlId == 5000:  # List control
            # Update selected index and button positions
            self.update_button_positions()
            # Auto-focus Edit button when list gets focus, but only if not coming from Edit/Delete buttons
            # This allows navigation between segments: when you press up/down from Edit button, 
            # it goes to list, then auto-focuses Edit for the new segment
            if (self._previous_focus is not None and 
                self._previous_focus not in [5021, 5022] and  # Not from Edit/Delete buttons
                len(self.segments) > 0):
                try:
                    # Small delay to ensure list selection is updated
                    import threading
                    def focus_edit_button():
                        import time
                        time.sleep(0.05)  # Small delay to let list selection settle
                        try:
                            edit_btn = self.getControl(5021)
                            if edit_btn and edit_btn.isVisible():
                                self.setFocusId(5021)
                                log(f"✅ Auto-focused Edit button (previous focus: {self._previous_focus})")
                        except:
                            pass
                    threading.Thread(target=focus_edit_button, daemon=True).start()
                except:
                    pass
        
        # Update previous focus for next time
        self._previous_focus = controlId
    
    def check_unsaved_changes(self):
        """Check if there are unsaved changes and prompt user if needed. Returns True if should exit, False if should cancel."""
        if not self.segments_modified:
            # No unsaved changes, safe to exit
            log("✅ No unsaved changes - safe to exit")
            return True
        
        # Has unsaved changes - show warning dialog with custom button labels
        log("⚠️ Unsaved changes detected - showing warning dialog")
        dialog = xbmcgui.Dialog()
        # Use only 2 positional args to avoid conflict with keyword args
        result = dialog.yesno(
            "Segment Editor",
            "You have unsaved changes.\nExit without saving?",
            yeslabel="Yes",
            nolabel="Cancel"
        )
        if result:
            log("✅ User confirmed exit without saving (clicked Yes)")
            self.segments_modified = False
            return True
        else:
            log("❌ User cancelled exit - staying in editor (clicked Cancel)")
            return False
    
    def jump_to_segment_start(self):
        """Jump playback to the start of the selected segment"""
        if self.selected_index < 0 or self.selected_index >= len(self.segments):
            log("⚠️ No segment selected to jump to")
            return
        
        seg = self.segments[self.selected_index]
        start_time = seg.start_seconds
        
        try:
            if self.player.isPlayingVideo():
                self.player.seekTime(start_time)
                log(f"⏩ Jumped to segment start: {start_time:.2f}s")
            else:
                log("⚠️ Cannot jump - video not playing")
        except Exception as e:
            log(f"❌ Error jumping to segment start: {e}")
    
    def seek_relative(self, seconds):
        """Seek forward or backward by specified seconds"""
        try:
            if self.player.isPlayingVideo():
                current = self.player.getTime()
                new_time = max(0, current + seconds)
                self.player.seekTime(new_time)
                log(f"⏩ Seeked {seconds:+d}s: {current:.2f} → {new_time:.2f}")
        except Exception as e:
            log(f"❌ Error seeking: {e}")
    
    def jump_to_time(self):
        """Jump to a specific time entered by the user"""
        try:
            if not self.player.isPlayingVideo():
                xbmcgui.Dialog().ok("Segment Editor", "Cannot jump - video is not playing.")
                return
            
            current = self.player.getTime()
            current_hms = seconds_to_hms(current)
            
            time_str = xbmcgui.Dialog().input(
                "Jump To Time (HH:MM:SS.mmm or seconds)",
                defaultt=current_hms
            )
            
            if not time_str:
                return  # User cancelled
            
            # Parse the time input
            try:
                if ":" in time_str:
                    target_time = hms_to_seconds(time_str)
                else:
                    target_time = float(time_str)
                
                if target_time < 0:
                    xbmcgui.Dialog().ok("Segment Editor", "Time cannot be negative.")
                    return
                
                self.player.seekTime(target_time)
                log(f"⏩ Jumped to time: {target_time:.2f}s ({seconds_to_hms(target_time)})")
                xbmcgui.Dialog().notification(
                    "Segment Editor",
                    f"Jumped to {seconds_to_hms(target_time)}",
                    icon=self.icon_path,
                    time=2000
                )
            except ValueError:
                xbmcgui.Dialog().ok("Segment Editor", "Invalid time format. Use HH:MM:SS.mmm or seconds.")
            except Exception as e:
                log(f"❌ Error jumping to time: {e}")
                xbmcgui.Dialog().ok("Segment Editor", f"Error: {str(e)}")
        except Exception as e:
            log(f"❌ Error in jump_to_time: {e}")
    
    def toggle_pause(self):
        """Toggle pause/play state"""
        try:
            if self.player.isPlayingVideo():
                # Toggle our tracked state immediately (we know what we're toggling to)
                self.is_paused = not self.is_paused
                
                # Call Kodi's pause() method which toggles pause/play
                self.player.pause()
                
                # Update button label immediately
                try:
                    pause_button = self.getControl(5018)
                    if pause_button:
                        # When playing (not paused = False), show "Pause"
                        # When paused (is_paused = True), show "Resume"
                        pause_button.setLabel("Pause" if not self.is_paused else "Resume")
                except:
                    pass
                
                if self.is_paused:
                    log("⏸️ Paused playback")
                else:
                    log("▶️ Resumed playback")
            else:
                log("⚠️ Cannot toggle pause - video is not playing")
        except Exception as e:
            log(f"❌ Error toggling pause: {e}")
    
    def set_as_start(self):
        """Mark current playback position as segment start (toggles if already marked)"""
        try:
            # Toggle: if start is already marked, clear it
            if self.pending_start_time is not None:
                log("📍 Start time already marked - clearing it")
                self.pending_start_time = None
                xbmcgui.Dialog().notification(
                    "Segment Editor",
                    "Start time cleared",
                    icon=self.icon_path,
                    time=2000
                )
                return
            
            if self.player.isPlayingVideo():
                new_start = self.player.getTime()
                
                # Validate: start must be before end if end is already set
                if self.pending_end_time is not None and new_start >= self.pending_end_time:
                    xbmcgui.Dialog().ok(
                        "Segment Editor",
                        f"Cannot set start time after end time.\n\n"
                        f"Current end: {seconds_to_hms(self.pending_end_time)}\n"
                        f"Attempted start: {seconds_to_hms(new_start)}\n\n"
                        f"Please set start time before end time, or clear end time first."
                    )
                    return
                
                self.pending_start_time = new_start
                log(f"📍 Marked start time: {self.pending_start_time:.2f}")
                xbmcgui.Dialog().notification(
                    "Segment Editor",
                    f"Start marked: {seconds_to_hms(self.pending_start_time)}",
                    icon=self.icon_path,
                    time=2000
                )
        except Exception as e:
            log(f"❌ Error marking start: {e}")
    
    def set_as_end(self):
        """Mark current playback position as segment end (toggles if already marked)"""
        try:
            # Toggle: if end is already marked, clear it
            if self.pending_end_time is not None:
                log("📍 End time already marked - clearing it")
                self.pending_end_time = None
                xbmcgui.Dialog().notification(
                    "Segment Editor",
                    "End time cleared",
                    icon=self.icon_path,
                    time=2000
                )
                return
            
            if self.player.isPlayingVideo():
                new_end = self.player.getTime()
                
                # Validate: end must be after start if start is already set
                if self.pending_start_time is not None and new_end <= self.pending_start_time:
                    xbmcgui.Dialog().ok(
                        "Segment Editor",
                        f"Cannot set end time before start time.\n\n"
                        f"Current start: {seconds_to_hms(self.pending_start_time)}\n"
                        f"Attempted end: {seconds_to_hms(new_end)}\n\n"
                        f"Please set end time after start time, or clear start time first."
                    )
                    return
                
                self.pending_end_time = new_end
                log(f"📍 Marked end time: {self.pending_end_time:.2f}")
                xbmcgui.Dialog().notification(
                    "Segment Editor",
                    f"End marked: {seconds_to_hms(self.pending_end_time)}",
                    icon=self.icon_path,
                    time=2000
                )
        except Exception as e:
            log(f"❌ Error marking end: {e}")
    
    def select_segment_from_list(self, title):
        """Show a dialog to select a segment from the list. Returns segment index or None if cancelled."""
        if not self.segments:
            xbmcgui.Dialog().ok("Segment Editor", "No segments available to select.")
            return None
        
        # Build list of segment descriptions
        options = []
        for i, seg in enumerate(self.segments):
            label = seg.raw_label if hasattr(seg, 'raw_label') else seg.segment_type_label
            start_hms = seconds_to_hms(seg.start_seconds)
            end_hms = seconds_to_hms(seg.end_seconds)
            options.append(f"Segment {i+1}: {label} ({start_hms} → {end_hms})")
        
        selected = xbmcgui.Dialog().select(title, options)
        if selected >= 0:
            return selected
        return None
    
    def start_at_end_of_segment(self):
        """Mark start point at the end of a selected segment"""
        if not self.segments:
            xbmcgui.Dialog().ok("Segment Editor", "No segments available.")
            return
        
        seg_index = self.select_segment_from_list("Select Segment (Start at End)")
        if seg_index is None:
            return  # User cancelled
        
        selected_seg = self.segments[seg_index]
        new_start = selected_seg.end_seconds
        
        # Validate: start must be before end if end is already set
        if self.pending_end_time is not None and new_start >= self.pending_end_time:
            xbmcgui.Dialog().ok(
                "Segment Editor",
                f"Cannot set start time after end time.\n\n"
                f"Current end: {seconds_to_hms(self.pending_end_time)}\n"
                f"Selected start: {seconds_to_hms(new_start)}\n\n"
                f"Please clear end time first or select a different segment."
            )
            return
        
        self.pending_start_time = new_start
        label = selected_seg.raw_label if hasattr(selected_seg, 'raw_label') else selected_seg.segment_type_label
        log(f"📍 Marked start time at end of segment {seg_index+1} ({label}): {self.pending_start_time:.2f}")
        xbmcgui.Dialog().notification(
            "Segment Editor",
            f"Start marked: {seconds_to_hms(self.pending_start_time)}",
            icon=self.icon_path,
            time=2000
        )
    
    def end_at_start_of_segment(self):
        """Mark end point at the start of a selected segment"""
        if not self.segments:
            xbmcgui.Dialog().ok("Segment Editor", "No segments available.")
            return
        
        seg_index = self.select_segment_from_list("Select Segment (End at Start)")
        if seg_index is None:
            return  # User cancelled
        
        selected_seg = self.segments[seg_index]
        new_end = selected_seg.start_seconds
        
        # Validate: end must be after start if start is already set
        if self.pending_start_time is not None and new_end <= self.pending_start_time:
            xbmcgui.Dialog().ok(
                "Segment Editor",
                f"Cannot set end time before start time.\n\n"
                f"Current start: {seconds_to_hms(self.pending_start_time)}\n"
                f"Selected end: {seconds_to_hms(new_end)}\n\n"
                f"Please clear start time first or select a different segment."
            )
            return
        
        self.pending_end_time = new_end
        label = selected_seg.raw_label if hasattr(selected_seg, 'raw_label') else selected_seg.segment_type_label
        log(f"📍 Marked end time at start of segment {seg_index+1} ({label}): {self.pending_end_time:.2f}")
        xbmcgui.Dialog().notification(
            "Segment Editor",
            f"End marked: {seconds_to_hms(self.pending_end_time)}",
            icon=self.icon_path,
            time=2000
        )
    
    def get_predefined_labels(self):
        """Get predefined labels from settings"""
        try:
            addon = get_addon()
            raw = addon.getSetting("predefined_labels")
            if raw:
                labels = [l.strip() for l in raw.split(",") if l.strip()]
                return labels
        except:
            pass
        # Default labels if setting is empty
        return ["Intro", "Recap", "Credits", "Commercial", "Ad", "Sponsor", "Outro"]
    
    def get_label_from_user(self, default=""):
        """Get label from user with predefined options"""
        predefined = self.get_predefined_labels()
        
        # Show selection dialog
        options = ["Custom..."] + predefined
        selected = xbmcgui.Dialog().select("Select Segment Label", options)
        
        if selected == 0:
            # User chose "Custom..."
            label = xbmcgui.Dialog().input(
                "Enter Custom Label",
                defaultt=default or "segment"
            )
            return label if label else (default or "segment")
        elif selected > 0:
            # User selected a predefined label
            return predefined[selected - 1]
        else:
            # User cancelled
            return None
    
    def add_with_marked_times(self):
        """Add a segment using the marked start and end times"""
        if self.pending_start_time is None or self.pending_end_time is None:
            xbmcgui.Dialog().ok(
                "Segment Editor",
                "Please mark both start and end times first.\n\n"
                "Use 'Set as Start' and 'Set as End' buttons while seeking."
            )
            return
        
        if self.pending_end_time <= self.pending_start_time:
            xbmcgui.Dialog().ok(
                "Segment Editor",
                "End time must be after start time."
            )
            return
        
        # Get label with predefined options
        label = self.get_label_from_user()
        if label is None:
            return  # User cancelled
        
        # Determine source type
        source = "edl"
        if self.segments and self.segments[0].source == "xml":
            source = "xml"
        
        new_seg = SegmentItem(
            self.pending_start_time,
            self.pending_end_time,
            label,
            source=source
        )
        self.segments.append(new_seg)
        self.segments.sort(key=lambda s: s.start_seconds)
        self.segments_modified = True
        
        # Clear markers
        self.pending_start_time = None
        self.pending_end_time = None
        
        self.refresh_list()
        log(f"✅ Added segment with marked times: {new_seg}")
        
        xbmcgui.Dialog().notification(
            "Segment Editor",
            "Segment added successfully",
            icon=self.icon_path,
            time=2000
        )
    
    def save_segments(self):
        """Save segments to file without closing the dialog"""
        log(f"💾 save_segments() called with video_path={self.video_path}, segments count={len(self.segments) if self.segments else 0}")
        
        if not self.video_path:
            log("❌ No video path available")
            xbmcgui.Dialog().ok("Segment Editor", "No video path available for saving.")
            return
        
        try:
            addon = get_addon()
            save_format_raw = addon.getSetting("save_format")
            log(f"📋 Save format setting (raw): {save_format_raw}")
            
            # Map display values to option values for labelenum
            format_map = {
                "Auto Detect": "auto",
                "EDL Only": "edl",
                "Chapter XML Only": "xml",
                "Both Formats": "both"
            }
            save_format = format_map.get(save_format_raw, save_format_raw.lower() if save_format_raw else "auto")
            log(f"📋 Save format (mapped): {save_format}")
            
            if not self.segments:
                log("❌ No segments to save")
                xbmcgui.Dialog().ok("Segment Editor", "No segments to save.")
                return
            
            log(f"📝 Segments to save: {[f'{s.start_seconds:.3f}-{s.end_seconds:.3f} ({s.segment_type_label})' for s in self.segments]}")
            
            edl_success = False
            xml_success = False
            
            # Determine what to save based on setting
            if save_format == "both":
                # Save to both formats - try both even if one fails
                edl_success = save_edl(self.video_path, self.segments)
                xml_success = save_chapters(self.video_path, self.segments)
                if edl_success and xml_success:
                    log("💾 Saved to both EDL and XML formats")
                elif edl_success:
                    log("💾 Saved to EDL format (XML save failed)")
                elif xml_success:
                    log("💾 Saved to XML format (EDL save failed)")
                else:
                    log("❌ Both EDL and XML saves failed")
            elif save_format == "xml":
                # Save to XML only
                xml_success = save_chapters(self.video_path, self.segments)
                if xml_success:
                    log("💾 Saved to XML format")
            elif save_format == "edl":
                # Save to EDL only
                edl_success = save_edl(self.video_path, self.segments)
                if edl_success:
                    log("💾 Saved to EDL format")
            else:  # auto
                # Auto-detect: try to save to existing format, or EDL if none
                # Check if chapters file exists
                import xbmcvfs
                base = os.path.splitext(self.video_path)[0]
                chapters_path = f"{base}-chapters.xml"
                if not xbmcvfs.exists(chapters_path):
                    chapters_path = f"{base}_chapters.xml"
                
                if xbmcvfs.exists(chapters_path):
                    xml_success = save_chapters(self.video_path, self.segments)
                    if xml_success:
                        log("💾 Auto-saved to XML format (existing file found)")
                else:
                    edl_success = save_edl(self.video_path, self.segments)
                    if edl_success:
                        log("💾 Auto-saved to EDL format (no existing file)")
            
            # Report success if at least one format saved successfully
            if edl_success or xml_success:
                self.segments_modified = False
                msg = "Segments saved successfully"
                if save_format == "both":
                    if edl_success and xml_success:
                        msg = "Segments saved to both formats"
                    elif edl_success:
                        msg = "Segments saved to EDL (XML failed)"
                    elif xml_success:
                        msg = "Segments saved to XML (EDL failed)"
                xbmcgui.Dialog().notification(
                    "Segment Editor",
                    msg,
                    icon=self.icon_path,
                    time=2000
                )
            else:
                xbmcgui.Dialog().ok("Segment Editor", "Failed to save segments. Check file permissions.")
        except Exception as e:
            log(f"❌ Error saving segments: {e}")
            import traceback
            log(f"Traceback: {traceback.format_exc()}")
            xbmcgui.Dialog().ok("Segment Editor", f"Error saving segments: {str(e)}")

