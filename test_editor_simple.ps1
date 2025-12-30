# Simple PowerShell script to trigger the segment editor
# Edit the username and password below

$kodiHost = "192.168.0.120"
$kodiPort = 6666
$username = "kodi"
$password = "kodi"

$uri = "http://${kodiHost}:${kodiPort}/jsonrpc"
$body = '{"jsonrpc":"2.0","method":"Addons.ExecuteAddon","params":{"addonid":"service.segmenteditor"},"id":1}'

$pair = "${username}:${password}"
$bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
$base64 = [System.Convert]::ToBase64String($bytes)
$auth = "Basic $base64"

$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = $auth
}

Invoke-WebRequest -Uri $uri -Method Post -Body $body -Headers $headers

