#!/bin/sh
# init-ssl.sh — Generate self-signed SSL certificates for bootstrap.
#
# On first deploy, run this script on the host to create certificates
# that nginx can use immediately. Replace with real Let's Encrypt certs
# before going to production (see scripts/ssl-letsencrypt.sh).
#
# Usage: ./scripts/init-ssl.sh [domain-or-ip]
#   Default domain: 185.92.180.219

set -e

DOMAIN="${1:-185.92.180.219}"
SSL_DIR="$(cd "$(dirname "$0")/.." && pwd)/ssl"

mkdir -p "$SSL_DIR"

# Generate a self-signed certificate valid for 365 days
openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout "$SSL_DIR/privkey.pem" \
  -out "$SSL_DIR/cert.pem" \
  -subj "/C=US/ST=State/L=City/O=MeetSync/CN=${DOMAIN}" \
  -addext "subjectAltName=DNS:${DOMAIN},IP:${DOMAIN}"

# Set restrictive permissions on the private key
chmod 600 "$SSL_DIR/privkey.pem"

echo "✅ Self-signed SSL certificates generated in ${SSL_DIR}/"
echo "   cert.pem  — public certificate"
echo "   privkey.pem — private key"
echo ""
echo "⚠  For production, replace these with Let's Encrypt certificates."
echo "   See scripts/ssl-letsencrypt.sh"
