#!/bin/sh
set -eu

case "${1:-}" in
    '') dry_run=0 ;;
    --dry-run) dry_run=1 ;;
    *) printf 'Usage: %s [--dry-run]\n' "$0" >&2; exit 2 ;;
esac
[ "$#" -le 1 ] || exit 2

BASE=${TWEET_SENTIMENT_HOME:-/opt/tweet-sentiment}
. "$BASE/host.env"
: "${ACME_WEBROOT:?}" "${CERT_DEST:?}" "${PROXY_CONTAINER:?}"

exec 9>"$BASE/certificate.lock"
flock -n 9 || exit 0

if [ "$dry_run" = 1 ]; then
    set -- renew --dry-run --non-interactive --no-random-sleep-on-renew
else
    set -- renew --quiet --non-interactive --no-random-sleep-on-renew
fi

"$BASE/certbot-venv/bin/certbot" "$@" \
    --config-dir "$BASE/tls" --work-dir "$BASE/certbot-work" \
    --logs-dir "$BASE/certbot-logs" --webroot-path "$ACME_WEBROOT"

[ "$dry_run" = 0 ] || exit 0
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
if docker exec "$PROXY_CONTAINER" nginx -t && \
    docker exec "$PROXY_CONTAINER" nginx -s reload; then
    exit 0
fi
mv "$CERT_DEST/fullchain.previous.pem" "$CERT_DEST/fullchain.pem"
mv "$CERT_DEST/privkey.previous.pem" "$CERT_DEST/privkey.pem"
docker exec "$PROXY_CONTAINER" nginx -t && \
    docker exec "$PROXY_CONTAINER" nginx -s reload || true
exit 1
