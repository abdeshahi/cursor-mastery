#!/bin/sh
# Public check — no credentials. Expect 401 = API ready.
set -eu
BASE="${WC_BASE_URL:-https://cttel.ir}"
code="000"
for _ in 1 2 3; do
  c=$(curl -sS --http1.1 --max-time 25 -o /dev/null -w '%{http_code}' "${BASE}/wp-json/wc/v3/products" 2>/dev/null || true)
  if [ -n "$c" ] && [ "$c" != "000" ]; then
    code="$c"
    break
  fi
  sleep 2
done
echo "GET ${BASE}/wp-json/wc/v3/products → HTTP ${code}"
if [ "$code" = "401" ] || [ "$code" = "200" ]; then
  echo "WooCommerce REST API: reachable"
  exit 0
fi
echo "Unexpected status — investigate CDN/origin"
exit 1
