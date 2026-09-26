#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
EXAMPLE_FILE="${ROOT_DIR}/.env.example"

rand() {
  openssl rand -base64 32 | tr -d '/+=' | head -c 24
}

if [[ -f "${ENV_FILE}" ]]; then
  echo ".env already exists — skipping generation."
  exit 0
fi

cp "${EXAMPLE_FILE}" "${ENV_FILE}"

sed -i "s/change-me-root-password/$(rand)/" "${ENV_FILE}"
sed -i "s/change-me-db-password/$(rand)/" "${ENV_FILE}"
sed -i "s/change-me-admin-password/$(rand)/" "${ENV_FILE}"

echo "Created ${ENV_FILE} with random passwords."
echo "Edit DOMAIN and LETSENCRYPT_EMAIL before requesting SSL."
