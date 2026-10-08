#!/usr/bin/env bash
# End-to-end check against a running stack (docker compose up -d --build).
set -euo pipefail
API=${API:-http://localhost:8000}

for i in $(seq 1 30); do
  curl -sf "$API/health" >/dev/null && break
  sleep 1
done
sleep 5  # let some prices arrive

curl -sf "$API/symbols" | grep -q AAPL
curl -sf "$API/prices/AAPL?limit=3" | grep -q '"price"'
curl -sf "$API/analytics/AAPL" | grep -q '"ma_5"'
curl -sf "$API/summary" >/dev/null
curl -sf "$API/summary" | grep -q '"cached":true'
[ "$(curl -s -o /dev/null -w '%{http_code}' "$API/prices/XYZ")" = 404 ]
echo "smoke test passed"
