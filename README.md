<img width="815" height="810" alt="icon" src="https://github.com/user-attachments/assets/a9f21f0f-75a8-4eed-90a0-64bf8ea6a2eb" />

# Segment Editor - Kodi Addon

A Kodi service addon that lets you edit EDL and Matroska chapter.xml
segment files while watching videos.

## Features

- **Full segment management**: add, edit, and delete segments during playback.
- **Multiple input methods**:
  - Quick add using marked start/end points.
  - Add at the current playback time with a user-set duration.
  - Manual entry of start and end times.
- **File format support**:
  - EDL (Edit Decision List) format (`.edl`).
  - Matroska chapter XML (`*-chapters.xml`, `*_chapters.xml`, `chapters.xml`).
  - **Embedded chapter import**: if a Matroska/WebM container has embedded
    chapters, the editor can import them on first edit (requires
    `mkvextract` on `PATH`).
  - Automatic detection prefers `chapters.xml` over `.edl` files.
- **Playback control**: pause/resume, precision seek
  (`-30s / -10s / -5s / -1s / +1s / +5s / +10s / +30s`), jump-to-time.
- **Time marking**: mark start and end points for precise segment creation,
  with validation that prevents invalid combinations.
- **Visual indicators**: segments marked *(Nested)* if fully contained
  within another segment, *(Overlapping)* if partially overlapping.
- **Label management**: configurable predefined labels with a custom-label
  escape hatch.
- **Keyboard shortcuts**: `Space`, `S`, `E`, `D`, `Enter`, `ESC`.
- **Real-time updates**: current time and pause state are pushed through
  `xbmc.Player` callbacks.
- **Auto-sort**: segments are automatically sorted by start time.

## Installation

1. Copy the `service.segmenteditor` folder to your Kodi addons directory and
   restart Kodi, **or**
2. Install the Skippy repo and install Segment Editor from there.

## Compatibility

Tested on Kodi **Omega 21.2** and **v22 Piers Alpha 2** across:

| Platform                  | Status   |
|---------------------------|----------|
| Android (Nvidia Shield)   | Tested   |
| Linux (CoreELEC)          | Tested   |
| Windows 11                | Tested   |

## Opening the editor

See [USAGE.md](USAGE.md) for the full walk-through of the keyboard
shortcut, remote-control key mapping via the *Keymap Editor* addon, and the
JSON-RPC / `NotifyAll` approach for scripting from SSH or other addons.

Quick reference:

- **Keyboard shortcut**: `CTRL` + a configurable key (default `CTRL+E`). The
  keymap file under `userdata/keymaps/keymap.xml` is generated and kept in
  sync by the service.
- **JSON-RPC**:

  ```json
  {"jsonrpc":"2.0",
   "method":"JSONRPC.NotifyAll",
   "params":{"sender":"service.segmenteditor",
             "message":"open_segment_editor"},
   "id":1}
  ```

## Using the editor

See [USAGE.md](USAGE.md#using-the-editor) for a detailed description of the
interface, every button, the keyboard shortcuts, and a worked workflow
example. The short version:

1. Seek to where you want a segment to start.
2. Click **Set as Start** (or press `S`).
3. Seek to where you want it to end.
4. Click **Set as End** (or press `E`).
5. Click **Create** and pick a label.
6. Click **Save** when you're done, then **Exit**.

### Time format

Times can be entered either as `HH:MM:SS.mmm` (for example `00:01:30.500`)
or as plain seconds (for example `90.5`). Negative values are rejected.

## File formats

### EDL

```
start_seconds    end_seconds    action_type
```

Example:

```
0.0    30.0    4
120.5  150.2   4
```

### Chapter XML

Matroska-style chapter XML files are supported with the following naming
conventions (preferred first):

- `{videoname}-chapters.xml`
- `{videoname}_chapters.xml`
- `{videoname}-chapter.xml`
- `{videoname}_chapter.xml`
- `chapters.xml` (in the same directory as the video)

When both a chapter XML and an EDL exist, the chapter XML is preferred.

## Settings

- **Predefined Segment Labels**: comma-separated labels that appear in the
  label dropdown when adding/editing segments.
- **Save Format**:
  - *Auto Detect*: uses the format of existing files, or EDL if none exist.
  - *EDL Only*: always save as `.edl`.
  - *Chapter XML Only*: always save as `-chapters.xml`.
  - *Both Formats*: save to both EDL and XML simultaneously.
- **Action Mapping**: comma-separated `action:label` pairs for the EDL
  third column (e.g. `4:Segment,5:Intro,6:Ad`).
- **Add rw permissions to saved files**: off by default; when enabled,
  additively grants group/other read+write on local saves.
- **Enable Full-Screen Dark Overlay**: darkens the entire video behind the
  editor dialog.

## Notes

- Segments are automatically sorted by start time.
- The editor can be opened while video is playing; playback continues in
  the background.
- Marked start/end times persist until a segment is added (they're used as
  defaults for the next segment).
- Validation prevents invalid start/end combinations.
- An "unsaved changes" warning appears when exiting with pending edits.

## Troubleshooting

- **Editor doesn't open**: make sure a video is currently playing.
- **Changes not saving**: check file permissions on the video directory.
- **No segments showing**: the video may not have a segment file yet - use
  **Add** / **Create** to create one.
- **Embedded chapter import skipped**: install `mkvmerge`/`mkvextract` so
  `mkvextract` is on `PATH`.

## Based on Skippy addon

This addon uses code patterns and segment parsing logic from the
[Skippy addon](https://github.com/jonnypuma/service.skippy) for consistency.
