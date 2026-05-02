# Changelog

## 1.2.5

### Improvements
- Default **Action Mapping** and **Predefined Segment Labels** now match **Skippy**’s extended `edl_action_mapping` (types 4–17: Segment through Cold_open) so new installs produce compatible `.edl` files without manual sync.

## 1.2.4

### Bug fixes
- **Chapter XML vs EDL**: Opening the editor tries chapter sidecars before EDL, but the reader previously stopped at the **first non-empty** XML file. If that file had no parseable `ChapterAtom` entries (placeholder, different layout, or empty edition), the addon fell back to EDL even when another XML path had valid chapters. The parser now **tries each known chapter path** until one yields segments.

## 1.2.3

### Improvements
- Segments are kept in **chronological order** (start time, then end time) when saving sidecars (`.edl` / chapter XML) **and** in the editor list whenever it refreshes. The highlighted segment stays selected after a re-sort when possible.

## 1.2.2

### Bug fixes
- **Edit / Delete next to segment list**: Restored syncing the side buttons with the highlighted row. Moving up/down in the list does not fire `onFocus` again (focus stays on control 5000), so selection and button position were stuck on the first segment. The dialog now re-syncs after list navigation and repositions the buttons to match the skin layout.

## 1.2.1

### Bug fixes
- **Shortcut / remote not opening editor**: Keymaps and `RunScript(service.segmenteditor)` run in a separate Python context from the background service. Sending only `NotifyAll` from that context did not reliably open the UI (the service subscribes to announcements, not the short-lived script). The editor now opens **directly** from `RunScript` via the new `editor_session` module; JSON-RPC `NotifyAll` still goes through the service as before.
- **`get_video_file()`**: Treats `Player.HasVideo` like Skippy when resolving the playing path, so shortcuts work during startup/buffering before `isPlayingVideo()` becomes true.
- **`onNotification`**: Avoids assuming `data` is a string (prevents handler errors on some announcements); wraps handler in a try/except.

## 1.2.0

### New Features
- **Import embedded chapters**: When the editor opens for a video that has no
  existing `.edl` or `chapter.xml` sidecar but does contain Matroska chapters,
  the editor offers to import them as segments. Requires `mkvextract` on the
  system `PATH`.

### IPC changes
- Replaced the `trigger_editor.txt` polling loop with Kodi's `NotifyAll` IPC.
  External triggers should now use JSON-RPC:

  ```json
  {"jsonrpc":"2.0",
   "method":"JSONRPC.NotifyAll",
   "params":{"sender":"service.segmenteditor",
             "message":"open_segment_editor"},
   "id":1}
  ```

  The old PowerShell / shell / batch test scripts that created trigger files
  have been removed.

### Internal / code-health improvements
- Consolidated the four separate entry scripts (`default.py`, `main.py`,
  `open_editor.py`, `trigger.py`) into a single shared `notify_open_editor()`
  helper. `trigger.py` has been removed.
- Replaced the regex-based `keymap.xml` rewriter with a proper
  `xml.etree.ElementTree` implementation (new `keymap_utils` module) so
  user comments, CDATA, and nested `<keyboard>` entries are preserved.
- Consolidated the four-way save-format branching into
  `segment_parser.save_segments()` and `delete_segment_files()`.
- De-duplicated the permission-setting logic inside
  `segment_parser.safe_file_write`; permission bits are now additive
  (`existing | 0o066`) rather than a blanket `chmod 0o666`.
- Pause/resume state is now driven by `xbmc.Player` callbacks instead of a
  background thread polling `getTime()` twice per second.
- Removed the custom `_explicit_click` dispatch guard; the dialog now relies
  on Kodi's native `onClick` callback.
- Dropped the manual `update_button_positions()` arithmetic for Edit/Delete
  buttons; they now operate on the currently selected list item from a fixed
  position.
- Replaced the `time.sleep(0.1)` inside the service's main loop with
  `monitor.waitForAbort(...)` so the service shuts down promptly.
- Replaced the per-keystroke `threading.Thread()` spawn in `onAction` with a
  lighter callback via `onFocus`.
- Cached the Kodi addon handle and the `enable_verbose_logging` flag so
  hot paths no longer re-read settings on every log call.
- Log lines no longer contain emoji, which breaks on some legacy Windows
  consoles.

### Bug fixes
- `hms_to_seconds()` now raises `ValueError` on negative, empty, or otherwise
  malformed input (previously `-00:00:10` silently parsed as `10` seconds).
- `SegmentItem` now rejects zero-duration segments (`end <= start`) as well
  as `end < start`, to match the dialog-level validation.
- Editing a segment's label now clears the cached EDL `action_type`, so EDL
  saves fall back to the user's Action Mapping / default `4` instead of
  silently reusing the stale numeric action.
- Segment icon path is now resolved via `addon.getAddonInfo('icon')` instead
  of a hardcoded `icon.png` join, which is more portable.

### Settings changes
- `Set File Permissions` is now disabled by default and renamed to
  "Add rw permissions to saved files (group + other)". When enabled, it now
  adds the `0o066` bits to whatever the file already has rather than
  stomping over the existing permissions with `0o666`.

## 1.1.2

### Bug Fixes
- Fixed EDL save: Action codes now follow the segment label and **Action Mapping** setting when the label is mapped (e.g. Intro, Credits). Previously, a value loaded from the file (such as Kodi’s internal type `2`) was kept even after changing the label in the editor, so the `.edl` third column did not match Skippy-compatible types

## 1.1.1

### Bug Fixes
- Fixed log spam: Filtered out noisy notifications (AudioLibrary.OnUpdate, VideoLibrary.OnUpdate, GUI events, etc.) to prevent hundreds of log entries

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

