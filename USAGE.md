# How to Open the Segment Editor During Playback

The segment editor can be opened in several ways while a video is playing:

## Method 1: Keyboard Shortcut (Recommended)

The addon automatically generates and updates a keymap file in your Kodi userdata directory. The keyboard shortcut key can be configured in the addon settings.

1. Configure the shortcut key in addon settings (default is `E`, which becomes `CTRL+E`)
2. The keymap file is automatically created/updated at:
   - **Windows**: `%APPDATA%\Kodi\userdata\keymaps\keymap.xml`
   - **Linux**: `~/.kodi/userdata/keymaps/keymap.xml`
   - **macOS**: `~/Library/Application Support/Kodi/userdata/keymaps/keymap.xml`
   - **Android**: `/sdcard/Android/data/org.xbmc.kodi/files/.kodi/userdata/keymaps/keymap.xml`
3. Press **CTRL+[your configured key]** during video playback to open the editor (e.g., `CTRL+E` if you set the key to `E`)
4. The keyboard shortcut always uses the CTRL modifier to avoid conflicts with Kodi's default keybindings
5. The keymap includes Global, FullscreenVideo, and VideoOSD sections for maximum compatibility

## Method 1b: Remote Control Key (Using Keymap Editor Addon)

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

## Method 2: JSON-RPC Call (May not work with service addons)

**Note:** Service addons may not respond correctly to `Addons.ExecuteAddon`. Try Method 2b (Trigger File) instead.

You can try to trigger the editor programmatically using Kodi's JSON-RPC API:

```json
{
  "jsonrpc": "2.0",
  "method": "Addons.ExecuteAddon",
  "params": {
    "addonid": "service.segmenteditor",
    "params": ["open_editor"]
  },
  "id": 1
}
```

**Windows PowerShell (Method 1 - Execute Script directly):**
```powershell
$uri = "http://192.168.0.120:6666/jsonrpc"
$body = '{"jsonrpc":"2.0","method":"Addons.ExecuteAddon","params":{"addonid":"service.segmenteditor","wait":false},"id":1}'
$username = "kodi"
$password = "kodi"
$pair = "${username}:${password}"
$bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
$base64 = [System.Convert]::ToBase64String($bytes)
$auth = "Basic $base64"
$headers = @{"Content-Type"="application/json"; "Authorization"=$auth}
Invoke-WebRequest -Uri $uri -Method Post -Body $body -Headers $headers
```

**Windows PowerShell (Method 2 - Use XBMC.RunScript if available):**
```powershell
$uri = "http://192.168.0.120:6666/jsonrpc"
$body = '{"jsonrpc":"2.0","method":"XBMC.RunScript","params":{"script":"service.segmenteditor","args":[]},"id":1}'
$username = "kodi"
$password = "kodi"
$pair = "${username}:${password}"
$bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
$base64 = [System.Convert]::ToBase64String($bytes)
$auth = "Basic $base64"
$headers = @{"Content-Type"="application/json"; "Authorization"=$auth}
Invoke-WebRequest -Uri $uri -Method Post -Body $body -Headers $headers
```

**Windows Command Prompt (using curl.exe):**
```cmd
curl.exe -X POST http://192.168.0.120:6666/jsonrpc -H "Content-Type: application/json" -H "Authorization: Basic a29kaTprb2Rp" -d "{\"jsonrpc\":\"2.0\",\"method\":\"Addons.ExecuteAddon\",\"params\":{\"addonid\":\"service.segmenteditor\"},\"id\":1}"
```
(Note: Replace "a29kaTprb2Rp" with your base64-encoded username:password)

**Linux/Mac:**
```bash
curl -X POST http://192.168.0.120:6666/jsonrpc -u kodi:kodi -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"Addons.ExecuteAddon","params":{"addonid":"service.segmenteditor"},"id":1}'
```

## Method 2b: Trigger File (Alternative - More Reliable)

The service monitors for a trigger file. Create this file to open the editor:

**Windows PowerShell:**
```powershell
New-Item -Path "$env:APPDATA\Kodi\addons\service.segmenteditor\trigger_editor.txt" -ItemType File -Force
```

**Linux/macOS:**
```bash
touch ~/.kodi/addons/service.segmenteditor/trigger_editor.txt
```

**CoreELEC/LibreELEC SSH (Recommended for Embedded Devices):**
```bash
touch /storage/.kodi/addons/service.segmenteditor/trigger_editor.txt
```

The background service monitors this file and will open the editor when it detects the file. The file is automatically deleted after the editor opens.

## Method 3: Context Menu (Advanced)

You can add a context menu item by creating a `context.xml` file, but this requires additional setup and is more complex.

## Troubleshooting

- **Editor doesn't open**: Make sure a video is currently playing
- **Keyboard shortcut doesn't work**: 
  - Check that keymap.xml is in the correct location
  - Verify the file format is correct XML
  - Make sure the addon is installed and enabled
  - Try restarting Kodi after adding the keymap
  - Check Kodi's log file for errors (look for "[service.segmenteditor]")
  - Try using JSON-RPC method instead (see Method 2 above)
- **Script error**: Check Kodi's log file for detailed error messages
- **No logs appear**: If pressing 'E' produces no logs at all, the keymap might not be loading. Try:
  - Verifying the keymap.xml file is in the correct userdata/keymaps/ directory
  - Checking that the XML is well-formed (no syntax errors)
  - Restarting Kodi completely (not just reloading)

## Notes

- The editor works while video is playing - playback continues in the background
- The editor automatically detects existing segment files (.edl or .xml)
- If no segment file exists, you can create one using the "Add" button

