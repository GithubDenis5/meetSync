#!/bin/sh
# wait-for-it.sh — wait for a TCP host:port to be available

HOST="$1"
PORT="$2"
TIMEOUT="${3:-30}"

if [ -z "$HOST" ] || [ -z "$PORT" ]; then
  echo "Usage: $0 host port [timeout]"
  exit 1
fi

echo "Waiting for $HOST:$PORT (timeout: ${TIMEOUT}s)..."
for i in $(seq 1 "$TIMEOUT"); do
  nc -z "$HOST" "$PORT" 2>/dev/null && echo "Ready!" && exit 0
  sleep 1
done
echo "Timeout waiting for $HOST:$PORT"
exit 1
