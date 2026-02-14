#!/usr/bin/env bash
set -euo pipefail

echo "Starting services..."
docker compose up -d

echo "Waiting for tunnel URL..."
TUNNEL_URL=""
for i in $(seq 1 30); do
    TUNNEL_URL=$(docker compose logs cloudflared 2>&1 \
        | grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' \
        | tail -1) || true
    if [ -n "$TUNNEL_URL" ]; then
        break
    fi
    sleep 2
done

if [ -z "$TUNNEL_URL" ]; then
    echo "ERROR: Could not detect tunnel URL after 60 seconds."
    echo "Check: docker compose logs cloudflared"
    exit 1
fi

echo "Tunnel URL: $TUNNEL_URL"

# Detect repo from gh CLI
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Repo: $REPO"

# Build server.json content
SERVER_JSON=$(cat <<EOF
{
  "name": "$(echo "$REPO" | cut -d/ -f1)",
  "url": "$TUNNEL_URL"
}
EOF
)

echo "Updating server.json on GitHub Pages..."

# Get current file SHA (if it exists)
SHA=$(gh api "repos/$REPO/contents/element/server.json" --jq .sha 2>/dev/null || echo "")

# Base64 encode the content
CONTENT_B64=$(echo -n "$SERVER_JSON" | base64 -w 0)

# Build the API payload
if [ -n "$SHA" ]; then
    PAYLOAD=$(printf '{"message":"Update tunnel URL","content":"%s","sha":"%s"}' "$CONTENT_B64" "$SHA")
else
    PAYLOAD=$(printf '{"message":"Update tunnel URL","content":"%s"}' "$CONTENT_B64")
fi

gh api -X PUT "repos/$REPO/contents/element/server.json" \
    --input - <<< "$PAYLOAD" > /dev/null

echo "Published: $TUNNEL_URL"
echo ""
echo "Synapse:  http://localhost:8008"
echo "Element:  http://localhost:8080"
echo "Tunnel:   $TUNNEL_URL"
