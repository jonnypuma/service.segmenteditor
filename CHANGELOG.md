# Changelog

## 1.1.0

### New Features
- Added "Jump To" button: Jump to a specific time by entering it manually (supports HH:MM:SS.mmm or seconds format)
- Added "Start at End of Segment" button: Set start point to the end of an existing segment via dialog selection
- Added "End at Start of Segment" button: Set end point to the start of an existing segment via dialog selection
- Toggle behavior for "Set as Start" and "Set as End" buttons: Press again to clear the marked time

### Improvements
- Renamed "Add with Marked Times" button to "Create" for clarity
- Improved button spacing: Consistent 8px gaps between buttons on seek row
- Improved bottom row alignment: Centered horizontally with 20px margins on both sides
- Made "Add Manual Start and End Points" button wider (250px) to fully display text
- Made Pause/Resume button wider (75px) for better visibility
- Better organization: "Jump To" button placed on far left of bottom row, "Exit" always on far right

### UI/UX Enhancements
- All buttons properly aligned and spaced for better visual consistency
- Improved horizontal alignment of all button rows with background panel

## 1.0.3

### Bug Fixes
- Added warning dialog error when exiting with unsaved changes (TypeError with yes/no dialog arguments)

## 1.0.2

### Changes
- Added darkening overlay behind bottom button rows (seek row and action row) for improved visibility
- Added warning dialog when exiting with unsaved changes
- Press Enter/Select on a list item to jump playback to the start of that segment

## 1.0.1

### Changes
- Updated provider name

## 1.0.0 (Initial Release)

### Features
- Edit EDL and chapter.xml segment files during video playback
- Add, edit, and delete segments
- Add segments at current playback time
- Automatic file format detection (EDL vs XML)
- Keyboard shortcut support via keymap.xml
- Dialog-based editor interface

### Technical Details
- Based on segment parsing logic from Skippy addon
- Uses Kodi's WindowXMLDialog for UI
- Supports both Matroska chapter XML and MPlayer EDL formats
- Service addon that monitors video playback

