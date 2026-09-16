#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

printf '\n== Artemis Agent deploy ==\n'

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: Node.js is required. Install Node 20+ first." >&2
  exit 1
fi

NODE_MAJOR="$(node -p "process.versions.node.split('.')[0]")"
if [ "$NODE_MAJOR" -lt 20 ]; then
  echo "ERROR: Node.js 20+ required. Current: $(node -v)" >&2
  exit 1
fi

if command -v pnpm >/dev/null 2>&1; then
  PM="pnpm"
elif command -v npm >/dev/null 2>&1; then
  PM="npm"
else
  echo "ERROR: npm or pnpm is required." >&2
  exit 1
fi

echo "Package manager: $PM"
echo "Working directory: $APP_DIR"

if [ "$PM" = "pnpm" ]; then
  pnpm install
  pnpm run test
  pnpm run build
else
  npm install
  npm run test
  npm run build
fi

mkdir -p dist/deploy
cat > dist/deploy/artemis.env.example <<'ENV'
ARTEMIS_BACKEND_URL=http://127.0.0.1:8642
ARTEMIS_PROFILE=default
ARTEMIS_LOG_LEVEL=info
ENV

printf '\nArtemis Agent deploy completed.\n'
printf 'Build output: %s/dist\n' "$APP_DIR"
