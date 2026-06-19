#!/bin/bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This script verifies both STDIO and StreamableHTTP transport handshakes
# for the selected Go MCP server module locally.

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MODULE_DIR=${1:-"mcp-nanobanana-go"}
BIN_NAME="mcp-test-bin"
PORT=9091

# Resolve Project ID
if [[ -z "${GOOGLE_CLOUD_PROJECT}" ]]; then
  export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null)
  if [[ -z "${GOOGLE_CLOUD_PROJECT}" ]]; then
    echo -e "${RED}ERROR: GOOGLE_CLOUD_PROJECT environment variable not set.${NC}"
    exit 1
  fi
fi

if [ ! -d "$MODULE_DIR" ]; then
  echo -e "${RED}ERROR: Module directory '$MODULE_DIR' does not exist.${NC}"
  exit 1
fi

echo -e "${BLUE}=== Starting Transport Validation for $MODULE_DIR ===${NC}"

# Compile temporary binary
echo -e "${YELLOW}Compiling $MODULE_DIR...${NC}"
if ! go build -o ./${MODULE_DIR}/${BIN_NAME} ./${MODULE_DIR}; then
  echo -e "${RED}ERROR: Compilation failed.${NC}"
  exit 1
fi

cleanup() {
  if [ -f "./${MODULE_DIR}/${BIN_NAME}" ]; then
    rm "./${MODULE_DIR}/${BIN_NAME}"
  fi
}
trap cleanup EXIT

# ------------------------------------------------------------------------------
# Test 1: STDIO Handshake
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[Test 1/2] Verifying STDIO Transport Handshake...${NC}"

STDIO_PAYLOAD='{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}'

RESPONSE=$(echo "$STDIO_PAYLOAD" | ./${MODULE_DIR}/${BIN_NAME} -transport stdio 2>/dev/null)

if echo "$RESPONSE" | grep -F '"result"' | grep -F '"protocolVersion"' &>/dev/null; then
  echo -e "${GREEN}PASS: STDIO handshake completed successfully!${NC}"
  echo "Response: $RESPONSE"
else
  echo -e "${RED}FAIL: STDIO handshake failed or returned invalid response.${NC}"
  echo "Raw Response: $RESPONSE"
  exit 1
fi

# ------------------------------------------------------------------------------
# Test 2: Streamable HTTP Handshake
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[Test 2/2] Verifying Streamable HTTP Transport Handshake...${NC}"

# Start HTTP server in the background
./${MODULE_DIR}/${BIN_NAME} -transport http -port ${PORT} &>/dev/null &
SERVER_PID=$!

# Ensure background server is terminated on exit
trap "kill $SERVER_PID &>/dev/null; cleanup" EXIT

# Wait for server to bind
sleep 1.5

# Send initialize request to HTTP endpoint
HTTP_INIT_RESPONSE=$(curl -s -i -X POST http://localhost:${PORT}/mcp \
  -H "Content-Type: application/json" \
  -d "$STDIO_PAYLOAD")

# Parse Mcp-Session-Id header (case insensitive)
SESSION_HEADER=$(echo "$HTTP_INIT_RESPONSE" | grep -i "Mcp-Session-Id:")
SESSION_ID=$(echo "$SESSION_HEADER" | awk '{print $2}' | tr -d '\r')

# Parse HTTP status
HTTP_STATUS=$(echo "$HTTP_INIT_RESPONSE" | head -n 1 | awk '{print $2}')

if [[ "$HTTP_STATUS" == "200" ]] && [[ -n "$SESSION_ID" ]]; then
  echo -e "${GREEN}PASS: HTTP Initialize succeeded!${NC}"
  echo "Acquired Session ID: $SESSION_ID"
  
  # Send tools/list request to verify session persistence
  LIST_PAYLOAD='{"jsonrpc":"2.0","method":"tools/list","id":2,"params":{}}'
  
  HTTP_LIST_RESPONSE=$(curl -s -X POST http://localhost:${PORT}/mcp \
    -H "Content-Type: application/json" \
    -H "Mcp-Session-Id: $SESSION_ID" \
    -d "$LIST_PAYLOAD")
    
  if echo "$HTTP_LIST_RESPONSE" | grep -F '"tools"' &>/dev/null; then
    echo -e "${GREEN}PASS: HTTP tools/list succeeded!${NC}"
  else
    echo -e "${RED}FAIL: HTTP tools/list request failed.${NC}"
    echo "Raw response: $HTTP_LIST_RESPONSE"
    exit 1
  fi
else
  echo -e "${RED}FAIL: HTTP Initialize failed.${NC}"
  echo "HTTP Status: $HTTP_STATUS"
  echo "Acquired Session ID: $SESSION_ID"
  echo "Full Headers Output:"
  echo "$HTTP_INIT_RESPONSE" | head -n 15
  exit 1
fi

echo -e "\n${GREEN}=== All Transport Handshake Validations PASSED ===${NC}"
