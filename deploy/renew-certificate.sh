#!/bin/sh
set -eu

BASE=/opt/tweet-sentiment
. "$BASE/host.env"
: "${ACME_WEBROOT:?}" "${CERT_DEST:?}" "${PROXY_CONTAINER:?}"

exec 9>/run/lock/tweet-sentiment-certificate.lock
flock -n 9 || exit 0

if [ "${1:-}" = "--dry-run" ]; then
    set -- renew --dry-run
else
    set -- renew --quiet
fi

docker run --rm --cpus=0.5 --memory=256m \
    -v "$BASE/tls:/etc/letsencrypt" \
    -v "$BASE/certbot-work:/var/lib/letsencrypt" \
    -v "$BASE/certbot-logs:/var/log/letsencrypt" \
    -v "$ACME_WEBROOT:/acme" \
    certbot/certbot@sha256:f70ad0adbb7e117f0fe42a63c553f28ea451edabc0148757b6efcd9735acaa20 \
    "$@"

[ "${2:-}" != "--dry-run" ] || exit 0
SOURCE="$BASE/tls/live/tweet-sentiment"
if cmp -s "$SOURCE/fullchain.pem" "$CERT_DEST/fullchain.pem" && \
    cmp -s "$SOURCE/privkey.pem" "$CERT_DEST/privkey.pem"; then
    exit 0
fi

# Keep the previous pair until nginx has accepted the renewed certificate.
cp -p "$CERT_DEST/fullchain.pem" "$CERT_DEST/fullchain.previous.pem"
cp -p "$CERT_DEST/privkey.pem" "$CERT_DEST/privkey.previous.pem"
install -m 644 "$SOURCE/fullchain.pem" "$CERT_DEST/fullchain.next.pem"
install -m 600 "$SOURCE/privkey.pem" "$CERT_DEST/privkey.next.pem"
mv "$CERT_DEST/fullchain.next.pem" "$CERT_DEST/fullchain.pem"
mv "$CERT_DEST/privkey.next.pem" "$CERT_DEST/privkey.pem"
if ! docker exec "$PROXY_CONTAINER" nginx -t; then
    mv "$CERT_DEST/fullchain.previous.pem" "$CERT_DEST/fullchain.pem"
    mv "$CERT_DEST/privkey.previous.pem" "$CERT_DEST/privkey.pem"
    exit 1
fi
docker exec "$PROXY_CONTAINER" nginx -s reload
