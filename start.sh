#!/usr/bin/env bash
set -euo pipefail

POLL_INTERVAL=60

# Detect repo once at startup
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
NODE_NAME=$(echo "$REPO" | cut -d/ -f1)

get_tunnel_url() {
    docker compose logs cloudflared 2>&1 \
        | grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' \
        | tail -1 || true
}

publish_url() {
    local url="$1"
    local server_json
    server_json=$(printf '{\n  "name": "%s",\n  "url": "%s"\n}\n' "$NODE_NAME" "$url")

    # Write locally
    echo "$server_json" > server.json

    # Push to GitHub
    local sha
    sha=$(gh api "repos/$REPO/contents/server.json" --jq .sha 2>/dev/null || echo "")

    local content_b64
    content_b64=$(echo -n "$server_json" | base64 -w 0)

    local payload
    if [ -n "$sha" ]; then
        payload=$(printf '{"message":"Update tunnel URL","content":"%s","sha":"%s"}' "$content_b64" "$sha")
    else
        payload=$(printf '{"message":"Update tunnel URL","content":"%s"}' "$content_b64")
    fi

    gh api -X PUT "repos/$REPO/contents/server.json" \
        --input - <<< "$payload" > /dev/null
}

# Start services
echo "Starting services..."
docker compose up -d

# Wait for initial tunnel URL
echo "Waiting for tunnel URL..."
CURRENT_URL=""
for i in $(seq 1 30); do
    CURRENT_URL=$(get_tunnel_url)
    if [ -n "$CURRENT_URL" ]; then
        break
    fi
    sleep 2
done

if [ -z "$CURRENT_URL" ]; then
    echo "ERROR: Could not detect tunnel URL after 60 seconds."
    echo "Check: docker compose logs cloudflared"
    exit 1
fi

echo "Publishing: $CURRENT_URL"
publish_url "$CURRENT_URL"

echo ""
echo "Synapse:  http://localhost:8008"
echo "Element:  http://localhost:8080"
echo "Tunnel:   $CURRENT_URL"
echo ""
echo "Watching for tunnel URL changes every ${POLL_INTERVAL}s... (Ctrl+C to stop)"

# Watch for URL changes
while true; do
    sleep "$POLL_INTERVAL"
    NEW_URL=$(get_tunnel_url)
    if [ -n "$NEW_URL" ] && [ "$NEW_URL" != "$CURRENT_URL" ]; then
        echo "$(date '+%H:%M:%S') Tunnel URL changed: $NEW_URL"
        publish_url "$NEW_URL"
        echo "$(date '+%H:%M:%S') Published."
        CURRENT_URL="$NEW_URL"
    fi
done
