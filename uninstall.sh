#!/bin/bash
set -e

cd "$(dirname "$0")/outomail"

echo "🗑️  outomail 제거..."

podman-compose down -v

rm -rf data

echo "✅ 제거 완료!"
