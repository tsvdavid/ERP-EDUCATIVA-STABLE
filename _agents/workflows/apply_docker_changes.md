---
description: How to correctly apply Docker container changes and fix the white screen issue
---

Whenever you make changes to the frontend or backend code and need to rebuild the containers in production, follow these steps to ensure the changes are applied correctly and the public URL (Cloudflare tunnel) does not suffer from cached IP issues (which cause a blank screen).

1. Rebuild the modified container (e.g., frontend or backend). Note: modify the command if you only want to rebuild the backend.
// turbo
`docker compose -f /var/www/erpeducativa/ERP-EDUCATIVA/docker-compose.prod.yml up -d --build frontend backend`

2. Restart the Cloudflared tunnel immediately after the rebuild finishes to flush its DNS cache, so it can discover the new internal IP of the recreated containers. If you skip this step, the frontend will show a blank screen on the public domain.
// turbo
`docker compose -f /var/www/erpeducativa/ERP-EDUCATIVA/docker-compose.yml restart tunnel`
