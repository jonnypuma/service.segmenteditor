# How to Open the Segment Editor During Playback

The segment editor can be opened in several ways while a video is playing:

## Method 1: Keyboard Shortcut (Recommended)

1. Copy the `keymap.xml` file to your Kodi userdata keymaps directory:
   - **Windows**: `%APPDATA%\Kodi\userdata\keymaps\keymap.xml`
   - **Linux**: `~/.kodi/userdata/keymaps/keymap.xml`
   - **macOS**: `~/Library/Application Support/Kodi/userdata/keymaps/keymap.xml`
   - **Android**: `/sdcard/Android/data/org.xbmc.kodi/files/.kodi/userdata/keymaps/keymap.xml`

2. If you already have a `keymap.xml` file, merge the contents instead of overwriting.

3. Press **E** during video playback to open the editor.

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
# Edit the path to match your Kodi addons directory
$triggerFile = "C:\Users\stone\AppData\Roaming\Kodi\addons\service.segmenteditor\trigger_editor.txt"
New-Item -Path $triggerFile -ItemType File -Force
```

Or use the provided script:
```powershell
.\trigger_editor.ps1
```

The service will detect the file and open the editor (if a video is playing), then delete the trigger file.

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

