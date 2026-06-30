#!/bin/sh
# ssl-letsencrypt.sh — Obtain/renew Let's Encrypt SSL certificates.
#
# Run this on the production host once the domain resolves to it.
# Certificates are placed in the ssl/ directory and mounted into nginx.
#
# Prerequisites:
#   - Domain must resolve to this server (port 80 reachable for HTTP-01 challenge)
#   - certbot installed: apt install certbot  or  brew install certbot
#
# Usage: ./scripts/ssl-letsencrypt.sh <domain>

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <domain>"
  echo "Example: $0 meetsync.app"
  exit 1
fi

DOMAIN="$1"
SSL_DIR="$(cd "$(dirname "$0")/.." && pwd)/ssl"

mkdir -p "$SSL_DIR"

# Stop the existing nginx (it occupies port 80) or run certbot in standalone mode
# that conflicts. We'll use --webroot mode expecting a temporary directory.

# Issue/renew the certificate
certbot certonly --webroot \
  --webroot-path "$SSL_DIR/.challenge" \
  --domains "$DOMAIN" \
  --non-interactive \
  --agree-tos \
  --email "admin@${DOMAIN}" \
  --deploy-hook "cp /etc/letsencrypt/live/${DOMAIN}/fullchain.pem ${SSL_DIR}/cert.pem && cp /etc/letsencrypt/live/${DOMAIN}/privkey.pem ${SSL_DIR}/privkey.pem"

# Copy to our ssl directory
mkdir -p "$SSL_DIR"
cp "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" "$SSL_DIR/cert.pem"
cp "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" "$SSL_DIR/privkey.pem"
chmod 600 "$SSL_DIR/privkey.pem"

echo ""
echo "✅ Let's Encrypt certificates installed in ${SSL_DIR}/"
echo ""
echo "ℹ  Auto-renewal is managed by certbot's systemd timer."
echo "   The deploy-hook copies renewed certs to the ssl/ directory."
echo ""
echo "   After renewal, restart the frontend container:"
echo "     docker compose restart frontend"
