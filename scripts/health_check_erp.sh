#!/usr/bin/env bash

# health_check_erp.sh
# Checks basic health of ERP-EDUCATIVA services.
# Returns exit code 0 if all checks pass, non‑zero otherwise.

set -euo pipefail

# Helper to print status
status() {
  local name=$1
  local result=$2
  if [ "$result" -eq 0 ]; then
    echo "${name}: OK"
  else
    echo "${name}: KO"
  fi
  return $result
}

# Check Docker containers are running
docker_ps=$(docker compose -f docker-compose.dev.yml ps --services --filter "status=running" || true)
expected="db backend frontend redis tunnel"
missing=""
for svc in $expected; do
  if [[ ! " $docker_ps " =~ " $svc " ]]; then
    missing+="$svc "
  fi
done
if [ -z "$missing" ]; then
  status "Docker containers" 0
else
  echo "Missing containers: $missing"
  status "Docker containers" 1
fi

# Check Backend health endpoint
if curl -s -f http://localhost:8000/api/health/ > /dev/null; then
  status "Backend health" 0
else
  status "Backend health" 1
fi

# Check Frontend reachable
if curl -s -f http://localhost:5174 > /dev/null; then
  status "Frontend reachability" 0
else
  status "Frontend reachability" 1
fi

# Check Cloudflare tunnel container is up (service name tunnel)
if docker ps --filter "name=tunnel" --filter "status=running" | grep tunnel > /dev/null; then
  status "Cloudflare tunnel" 0
else
  status "Cloudflare tunnel" 1
fi

exit 0
