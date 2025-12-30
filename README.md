<img width="815" height="810" alt="icon" src="https://github.com/user-attachments/assets/a9f21f0f-75a8-4eed-90a0-64bf8ea6a2eb" />

# Segment Editor - Kodi Addon

A Kodi service addon that allows you to edit EDL and chapter.xml segment files while watching videos.

## Features

- **Full Segment Management**: Add, edit, and delete segments while watching videos
- **Multiple Input Methods**: 
  - Quick add using marked start/end points
  - Add at current playback time with user-set duration
  - Manual entry of start and end times
- **File Format Support**: 
  - EDL (Edit Decision List) format (.edl)
  - Matroska chapter XML format (-chapters.xml, _chapters.xml, chapters.xml)
  - Automatic detection prefers chapters.xml over .edl files
- **Playback Control**: 
  - Pause/resume video playback
  - Seek with precision (-30s, -10s, -5s, -1s, +1s, +5s, +10s, +30s)
  - Real-time current time display with pause indicator
- **Time Marking**: 
  - Mark start and end points for precise segment creation
  - Visual feedback in status area
  - Validation prevents invalid time combinations
- **Visual Indicators**: 
  - Segments marked as "(Nested)" if fully contained within another segment
  - Segments marked as "(Overlapping)" if partially overlapping with another segment
- **Label Management**: 
  - Predefined labels (configurable in settings)
  - Custom label support
- **Keyboard Shortcuts**: Quick access to common functions (Space, S, E, D, Enter, ESC)
- **Real-time Updates**: Current time and pause state update dynamically
- **Auto-sorting**: Segments automatically sorted by start time

## Installation

1. Copy the `service.segmenteditor` folder to your Kodi addons directory
2. Restart Kodi or install via Add-on Manager

## Usage

### Opening the Editor

**Option 1: Keyboard Shortcut (Recommended)**
The addon automatically generates and updates a keymap file in your Kodi userdata directory. The keyboard shortcut key can be configured in the addon settings.

1. Configure the shortcut key in addon settings (default is `E`, which becomes `CTRL+E`)
2. The keymap file is automatically created/updated at:
   - Windows: `%APPDATA%\Kodi\userdata\keymaps\keymap.xml`
   - Linux: `~/.kodi/userdata/keymaps/keymap.xml`
   - macOS: `~/Library/Application Support/Kodi/userdata/keymaps/keymap.xml`
3. Press **CTRL+[your configured key]** during video playback to open the editor (e.g., `CTRL+E` if you set the key to `E`)
4. The keyboard shortcut always uses the CTRL modifier to avoid conflicts with Kodi's default keybindings
5. The keymap includes Global, FullscreenVideo, and VideoOSD sections for maximum compatibility

**Alternative: Remote Control Key (Using Keymap Editor Addon)**
You can also use the Keymap Editor addon to assign a key on your TV remote to launch the editor:

1. Install the "Keymap Editor" addon from the Kodi repository
2. **For FullscreenVideo mode:**
   - Open Keymap Editor and navigate to FullscreenVideo mode
   - Go all the way down and choose Add-ons
   - Scroll down to Launch Segment Editor and press OK/Select button
   - Press the key on your remote that you want to use
3. **For VideoOSD mode (important for when OSD is open):**
   - Navigate to VideoOSD mode in Keymap Editor
   - Repeat the same steps: Add-ons → Launch Segment Editor → Press your remote key
4. **For Global mode (optional, for broader coverage):**
   - Navigate to Global mode in Keymap Editor
   - Repeat the same steps: Add-ons → Launch Segment Editor → Press your remote key
5. Go back to the start and save the keymap

**Note:** It's recommended to map the key in both FullscreenVideo and VideoOSD sections so the editor works whether the video OSD is open or not. The Global section is optional but provides even broader coverage.

This allows you to trigger the editor with a single button press on your TV remote during video playback.

**Option 2: PowerShell/Command Line (Fallback)**
If the keyboard shortcut doesn't work, you can manually trigger the editor by creating a trigger file:

**Windows PowerShell:**
```powershell
New-Item -Path "$env:APPDATA\Kodi\addons\service.segmenteditor\trigger_editor.txt" -ItemType File -Force
```

**Linux/macOS:**
```bash
touch ~/.kodi/addons/service.segmenteditor/trigger_editor.txt
```

The background service monitors this file and will open the editor when it detects the file. The file is automatically deleted after the editor opens.

**Option 3: CoreELEC/LibreELEC SSH (Recommended for Embedded Devices)**
For CoreELEC, LibreELEC, or other embedded Linux Kodi distributions, you can trigger the editor via SSH:

```bash
touch /storage/.kodi/addons/service.segmenteditor/trigger_editor.txt
```

The background service monitors this file and will open the editor when it detects the file. The file is automatically deleted after the editor opens.

**Option 4: JSON-RPC**
- Use Kodi's JSON-RPC API to trigger the editor programmatically

### Using the Editor

#### Interface Overview

The editor displays:
- **Segment List**: Shows all segments with segment number, label, start time, end time, duration, and source format (EDL/XML)
- **Current Time Display**: Shows the current playback position with `[PAUSED]` indicator when video is paused
- **Status Area**: Displays marked start/end times and validation warnings
- **Segment Indicators**: Segments are marked with "(Nested)" if fully contained within another segment, or "(Overlapping)" if they partially overlap with another segment
- **Darkening Overlay**: A semi-transparent overlay behind the bottom button rows improves visibility when the video background is bright

#### Main Functions

**1. View Segments**
- The list shows all segments from the current video's segment file
- Segments are automatically sorted by start time
- Edit and Delete buttons appear next to each segment (only visible when segments exist)

**2. Playback Controls**

- **Pause/Resume Button**: 
  - Click "Pause" when playing to pause the video for precise marking
  - Click "Resume" when paused to continue playback
  - The button text and `[PAUSED]` indicator update dynamically based on actual playback state
  - **Keyboard Shortcut**: Press `Space` while the segment list is focused

- **Seek Controls**: Navigate through the video with precision
  - `-30s`: Seek backward 30 seconds
  - `-10s`: Seek backward 10 seconds
  - `-5s`: Seek backward 5 seconds
  - `-1s`: Seek backward 1 second
  - `+1s`: Seek forward 1 second
  - `+5s`: Seek forward 5 seconds
  - `+10s`: Seek forward 10 seconds
  - `+30s`: Seek forward 30 seconds

**3. Mark Start/End Points**

- **Set as Start**: Marks the current playback position as the start of a segment
  - **Button**: Click "Set as Start" button
  - **Keyboard Shortcut**: Press `S` while the segment list is focused
  - The marked start time appears in the status area

- **Set as End**: Marks the current playback position as the end of a segment
  - **Button**: Click "Set as End" button
  - **Keyboard Shortcut**: Press `E` while the segment list is focused
  - The marked end time appears in the status area

- **Validation**: 
  - You cannot set start time after end time
  - You cannot set end time before start time
  - Invalid combinations show a warning in the status area

**4. Add Segments**

- **Add with Marked Times** (Quick Method):
  - Mark both start and end points first
  - Click "Add with Marked Times" to create a segment using the marked times
  - You'll be prompted to select or enter a label

- **Add at Current Time + User Set Time**:
  - Click this button to create a segment starting at the current playback position
  - You'll be prompted to enter:
    - Duration (default: 10 seconds)
    - Label (predefined options or custom)
  - The end time is calculated automatically

- **Add Manual Start and End Points**:
  - Click "Add Manual Start and End Points" to enter times manually
  - Marked times (if any) will be offered as defaults
  - You'll be prompted to enter:
    - Start time (HH:MM:SS.mmm or seconds)
    - End time (HH:MM:SS.mmm or seconds)
    - Label (predefined options or custom)

**5. Navigate to Segments**

- **Jump to Segment Start**: 
  - Select a segment in the list
  - Press `Enter` or `Select` to jump playback to the start of that segment
  - This allows you to quickly navigate to any segment in the video

**6. Edit Segments**

- **Edit Button**: 
  - Select a segment in the list (Edit and Delete buttons appear next to the selected segment)
  - Click "Edit" button (or press `Right` arrow to focus it, then `Enter`) to modify the segment
  - You can change start time, end time, and label
  - Marked times (if any) will be offered as defaults

**7. Delete Segments**

- **Delete Button**: 
  - Select a segment in the list
  - Click "Delete" to remove the selected segment
  - **Keyboard Shortcut**: Press `D` while the segment list is focused
  - A confirmation dialog will appear

- **Delete All Button**: 
  - Removes all segments from the file
  - Located in the bottom button row
  - A confirmation dialog will appear

**8. Save and Exit**

- **Save Button**: 
  - Saves all changes to the segment file
  - The file format is determined by your save format setting (EDL, XML, or both)
  - The dialog remains open after saving (you can continue editing)

- **Exit Button**: 
  - Closes the editor without saving changes (if any)
  - **Warning Dialog**: If you have unsaved changes, a warning dialog will appear asking if you want to exit without saving
  - **Keyboard Shortcut**: Press `ESC` or `Back` key (also shows warning if there are unsaved changes)

#### Keyboard Shortcuts

All keyboard shortcuts only work when the segment list is focused:

- `Space`: Toggle pause/play
- `S`: Set current position as start
- `E`: Set current position as end
- `D`: Delete selected segment
- `Enter`/`Select`: Jump playback to the start of the selected segment
- `Right` arrow: Focus the Edit button for the selected segment
- `ESC`/`Back`: Exit editor (discard changes)

#### Button Reference

**Top Row (Seek Controls)**:
- `-30s`, `-10s`, `-5s`, `-1s`, `+1s`, `+5s`, `+10s`, `+30s`: Seek buttons
- `Pause`/`Resume`: Playback control
- `Set as Start`: Mark start point
- `Set as End`: Mark end point
- `Add with Marked Times`: Create segment from marked times

**Bottom Row (Main Actions)**:
- `Add at Current Time + User Set Time`: Quick add at current position
- `Add Manual Start and End Points`: Manual entry method
- `Delete All`: Remove all segments
- `Save`: Save changes (keeps dialog open)
- `Exit`: Close editor without saving

### Workflow Example

1. Open the editor during video playback (press `CTRL+E` if keymap is configured with default key)
2. Navigate to where you want a segment to start using the seek buttons
3. Optionally pause the video for precise marking
4. Click "Set as Start" to mark the start position
5. Navigate to where you want the segment to end (seek forward/backward as needed)
6. Click "Set as End" to mark the end position
7. Click "Add with Marked Times" to create the segment
8. Select a label from the predefined list or enter a custom label
9. Repeat for additional segments
10. Click "Save" when done (segments will be saved according to your save format setting)
11. Click "Exit" to close the editor

### Time Format

You can enter times in either format:
- `HH:MM:SS.mmm` (e.g., `00:01:30.500`)
- Seconds as decimal (e.g., `90.5`)

## File Formats

### EDL Format
EDL files use the format:
```
start_seconds    end_seconds    action_type
```

Example:
```
0.0    30.0    4
120.5  150.2   4
```

### Chapter XML Format
Matroska-style chapter XML files are also supported. The addon supports multiple naming conventions:
- `{videoname}-chapters.xml` (preferred)
- `{videoname}_chapters.xml`
- `{videoname}-chapter.xml`
- `{videoname}_chapter.xml`
- `chapters.xml` (in the same directory as the video)

The addon automatically detects which format to use based on existing files, and **prefers chapters.xml over .edl files** when both exist.

## Settings

- **Predefined Segment Labels**: Configure comma-separated labels (e.g., "Intro,Recap,Credits") that appear in a dropdown when adding/editing segments
- **Save Format**: Choose to save segments as:
  - **Auto Detect**: Uses the format of existing files, or EDL if none exist
  - **EDL Only**: Always save as .edl file
  - **Chapter XML Only**: Always save as -chapters.xml file
  - **Both Formats**: Save to both EDL and XML files simultaneously

## Notes

- **File Format Priority**: The addon prefers chapters.xml files over .edl files when both exist
- **Auto-detection**: Automatically detects which format to use based on existing files (unless overridden in settings)
- **New Files**: If no segment file exists, the addon will create one based on your save format setting
- **Auto-sorting**: Segments are automatically sorted by start time when saved
- **Background Playback**: The editor can be opened while video is playing - playback continues in the background
- **Pause Detection**: The pause/play button and `[PAUSED]` indicator update dynamically based on actual playback state
- **Time Marking**: Marked start/end times persist until you add a segment (they're used as defaults for the next segment)
- **Validation**: The system prevents setting invalid start/end time combinations (start after end, end before start)
- **Edit/Delete Buttons**: Edit and Delete buttons are only visible when at least one segment exists
- **Segment Indicators**: Visual indicators show nested and overlapping segments for better organization
- **Unsaved Changes Warning**: A warning dialog appears when exiting with unsaved changes, preventing accidental data loss
- **Darkening Overlay**: Bottom button rows have a darkening overlay for improved visibility against bright video backgrounds

## Troubleshooting

- **Editor doesn't open**: Make sure a video is currently playing
- **Changes not saving**: Check file permissions on the video directory
- **No segments showing**: The video may not have a segment file yet - use "Add" to create one

## Based on Skippy Addon

This addon uses code patterns and segment parsing logic from the [Skippy addon](https://github.com/jonnypuma/service.skippy) for consistency.


