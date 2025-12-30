# Alternative method: Create a trigger file that the service will detect
# This works around JSON-RPC limitations with service addons

param(
    [string]$KodiAddonPath = "C:\Users\stone\AppData\Roaming\Kodi\addons\service.segmenteditor"
)

$triggerFile = Join-Path $KodiAddonPath "trigger_editor.txt"

# Create the trigger file
New-Item -Path $triggerFile -ItemType File -Force | Out-Null
Write-Host "Trigger file created. The editor should open if a video is playing."
Write-Host "Trigger file location: $triggerFile"

