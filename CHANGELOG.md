# Changelog

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

