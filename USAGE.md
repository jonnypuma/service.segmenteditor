# Using the Segment Editor

This guide covers two things:

1. [How to open the editor during playback](#opening-the-editor).
2. [What each button does once it's open](#using-the-editor).

---

## Opening the editor

The segment editor can be opened in several ways while a video is playing.

### Method 1: Keyboard shortcut (recommended)

The addon automatically generates and keeps `userdata/keymaps/keymap.xml`
in sync with the shortcut key configured in the addon settings.

1. Configure the shortcut key in addon settings (default `E`, which becomes
   `CTRL+E`).
2. The keymap file is created/updated at:
   - **Windows**: `%APPDATA%\Kodi\userdata\keymaps\keymap.xml`
   - **Linux**: `~/.kodi/userdata/keymaps/keymap.xml`
   - **macOS**: `~/Library/Application Support/Kodi/userdata/keymaps/keymap.xml`
   - **Android**: `/sdcard/Android/data/org.xbmc.kodi/files/.kodi/userdata/keymaps/keymap.xml`
3. Press `CTRL + <your configured key>` during video playback.
4. The binding always uses the `CTRL` modifier to avoid conflicts with
   Kodi's built-in keybindings.
5. The keymap includes `Global`, `FullscreenVideo`, and `VideoOSD` sections
   for maximum compatibility.

### Method 1b: Remote-control key (via the Keymap Editor addon)

1. Install the "Keymap Editor" addon from the Kodi repository.
2. **FullscreenVideo mode**: open Keymap Editor → FullscreenVideo → Add-ons,
   scroll to *Launch Segment Editor*, press OK, then press the key on your
   remote that you want to use.
3. **VideoOSD mode** (for when the OSD is open): repeat the same steps
   under the `VideoOSD` section.
4. **Global mode** (optional, broader coverage): repeat under `Global`.
5. Save the keymap.

It is recommended to map the key in both `FullscreenVideo` and `VideoOSD`
so the editor works whether or not the OSD is on-screen.

### Method 2: JSON-RPC (`NotifyAll`)

Service addons are best triggered via Kodi's `NotifyAll` IPC, which the
background service listens for.

```json
{"jsonrpc":"2.0",
 "method":"JSONRPC.NotifyAll",
 "params":{"sender":"service.segmenteditor",
           "message":"open_segment_editor"},
 "id":1}
```

**Windows PowerShell**:

```powershell
$uri = "http://192.168.0.120:6666/jsonrpc"
$body = '{"jsonrpc":"2.0","method":"JSONRPC.NotifyAll","params":{"sender":"service.segmenteditor","message":"open_segment_editor"},"id":1}'
$pair = "kodi:kodi"
$base64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{"Content-Type"="application/json"; "Authorization"="Basic $base64"}
Invoke-WebRequest -Uri $uri -Method Post -Body $body -Headers $headers
```

**Linux / macOS / CoreELEC (curl over SSH)**:

```bash
curl -X POST http://192.168.0.120:6666/jsonrpc \
     -u kodi:kodi \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"JSONRPC.NotifyAll","params":{"sender":"service.segmenteditor","message":"open_segment_editor"},"id":1}'
```

### Method 3: From another addon

Use the same mechanism as the keymap (recommended):

```python
import xbmc
xbmc.executebuiltin("RunScript(service.segmenteditor)")
```

From Python code running **inside** this addon you may call:

```python
from editor_session import open_segment_editor
open_segment_editor()
```

Or send ``JSONRPC.NotifyAll`` (see Method 2) so the background service opens
the editor.

Older examples used ``NotifyAll(service.segmenteditor,open_segment_editor)``;
that still works by routing through the service's notification handler.

### Legacy trigger files

Earlier versions watched for `addons/service.segmenteditor/trigger_editor.txt`
as a one-shot signal. That mechanism has been removed in 1.2.0 in favour of
`NotifyAll`; use the JSON-RPC payload above instead.

---

## Using the editor

Once the dialog is open you'll see:

- **Segment list**: every segment with its number, label, start, end,
  duration, and source format (`edl` / `xml`).
- **Current time display**: the playback position, with `[PAUSED]` when
  paused.
- **Status area**: marked start/end times and validation warnings.
- **Segment indicators**: *(Nested)* when fully contained in another
  segment, *(Overlapping)* when partially overlapping.

### Main functions

**Playback controls**

- **Pause / Resume**: toggles the video. Shortcut: `Space` (when the list
  is focused).
- **Seek**: `-30s`, `-10s`, `-5s`, `-1s`, `+1s`, `+5s`, `+10s`, `+30s`.
- **Jump To**: enter a time manually (`HH:MM:SS.mmm` or seconds).

**Marking start/end**

- **Set as Start** / **Set as End**: record the current playback position.
  Press again on either button to clear that mark. Keyboard shortcuts `S`
  and `E` when the list is focused.
- **Start at End of...** / **End at Start of...**: pick an existing
  segment to use its end (or start) time as the mark.
- Invalid combinations (start after end, end before start) are refused.

**Creating / editing**

- **Create**: create a segment from the marked start and end times.
- **Add at Current Time + User Set Time**: start at the current playback
  position and enter a duration.
- **Add Manual Start and End Points**: type both times manually.
- **Edit**: edits the currently selected segment.

**Navigating**

- `Enter` / `Select` on a list item jumps playback to that segment's
  start.
- `D` deletes the currently selected segment.

**Save and exit**

- **Save**: persists changes and keeps the dialog open.
- **Exit**: closes. If you have unsaved changes, a confirmation dialog is
  shown. `ESC` / `Back` does the same thing.

### Embedded chapter import

When the editor opens for a video with no existing EDL or chapter-XML
sidecar, it tries to read chapters embedded in the video container using
`mkvextract` (if available). If it finds any, it offers to import them as
segments. Install `mkvmerge` / `mkvtoolnix` to make this work on your
system.

### Keyboard shortcuts (when the list is focused)

| Key           | Action                                    |
|---------------|-------------------------------------------|
| `Space`       | Pause / resume                            |
| `S`           | Mark current position as start            |
| `E`           | Mark current position as end              |
| `D`           | Delete the selected segment               |
| `Enter`       | Jump playback to the selected segment     |
| `Right`       | Focus the Edit button for the selection   |
| `ESC` / `Back`| Exit (with unsaved-changes confirmation)  |

### Workflow example

1. Open the editor during playback (`CTRL+E` by default).
2. Seek to where you want a segment to start. Optionally pause.
3. Click **Set as Start** (or press `S`).
4. Seek to where you want it to end.
5. Click **Set as End** (or press `E`).
6. Click **Create** and pick a label.
7. Repeat for additional segments.
8. Click **Save** when done, then **Exit**.

---

## Troubleshooting

- **Editor doesn't open**: make sure a video is currently playing.
- **Keyboard shortcut doesn't work**:
  - Check that `keymap.xml` exists in the right `userdata/keymaps/`
    directory and is well-formed XML.
  - Verify the addon is installed and the service is running.
  - Restart Kodi completely.
  - Look for `[service.segmenteditor]` entries in `kodi.log`.
  - Try the JSON-RPC method above as a fallback.
- **Script error**: check `kodi.log` for the full stack trace.
- **Embedded chapter import skipped**: `mkvextract` is missing from
  `PATH`. Install `mkvtoolnix` / `mkvmerge` or skip the prompt.

## Notes

- The editor runs while video is playing; playback continues in the
  background.
- Existing `.edl` or chapter XML files are auto-detected.
- If no segment file exists, you can create one via **Create**, **Add at
  Current Time**, or **Add Manual Start and End Points**.
- `Enter` / `Select` on a list item jumps playback to that segment's
  start.
