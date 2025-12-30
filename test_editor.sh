#!/bin/bash
# Test script to trigger the segment editor via JSON-RPC

# Default Kodi JSON-RPC endpoint
KODI_HOST="localhost"
KODI_PORT="8080"

# Try to execute the addon script
curl -X POST "http://${KODI_HOST}:${KODI_PORT}/jsonrpc" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "Addons.ExecuteAddon",
    "params": {
      "addonid": "service.segmenteditor",
      "wait": false
    },
    "id": 1
  }'

echo ""

