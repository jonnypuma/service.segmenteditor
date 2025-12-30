# PowerShell script to trigger the segment editor via JSON-RPC
# Usage: .\test_editor.ps1 -Username "kodi" -Password "kodi"

param(
    [string]$KodiHost = "192.168.0.120",
    [int]$KodiPort = 6666,
    [string]$Username = "kodi",
    [string]$Password = "kodi"
)

$uri = "http://${KodiHost}:${KodiPort}/jsonrpc"
$body = @{
    jsonrpc = "2.0"
    method = "Addons.ExecuteAddon"
    params = @{
        addonid = "service.segmenteditor"
    }
    id = 1
} | ConvertTo-Json -Compress

$credential = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Basic $credential"
}

try {
    $response = Invoke-WebRequest -Uri $uri -Method Post -Body $body -Headers $headers
    Write-Host "Success: $($response.Content)"
} catch {
    Write-Host "Error: $_"
    Write-Host "Response: $($_.Exception.Response)"
}

