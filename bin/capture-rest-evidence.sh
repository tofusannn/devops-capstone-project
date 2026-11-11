#!/usr/bin/env bash
# Capture genuine API evidence from the running Accounts service.
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8080}"
mkdir -p evidence

curl -sSi -X POST "${BASE_URL}/accounts" \
  -H "Content-Type: application/json" \
  --data '{"name":"Capstone Evidence","email":"capstone@example.com","address":"Bangkok","date_joined":"2026-11-11"}' \
  | tee evidence/rest-create-done

# The ID below comes from a real create response; it is not hard-coded.
ACCOUNT_ID="$(sed -n '/^{/,$p' evidence/rest-create-done | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
curl -sSi "${BASE_URL}/accounts" | tee evidence/rest-list-done
curl -sSi "${BASE_URL}/accounts/${ACCOUNT_ID}" | tee evidence/rest-read-done
curl -sSi -X PUT "${BASE_URL}/accounts/${ACCOUNT_ID}" \
  -H "Content-Type: application/json" \
  --data '{"name":"Capstone Updated","email":"updated@example.com","address":"Chiang Mai","date_joined":"2026-11-11"}' \
  | tee evidence/rest-update-done
curl -sSi -X DELETE "${BASE_URL}/accounts/${ACCOUNT_ID}" \
  | tee evidence/rest-delete-done
echo "Saved genuine API responses under evidence/"
