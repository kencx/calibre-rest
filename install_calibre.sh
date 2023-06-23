#!/usr/bin/env bash

# install calibre to an x86_64 Linux system

set -euo pipefail

CALIBRE_DEST="${1:-/opt/calibre}"
CALIBRE_RELEASE=$(curl -sX GET "https://api.github.com/repos/kovidgoyal/calibre/releases/latest" |
    jq -r .tag_name)
CALIBRE_VERSION="$(echo ${CALIBRE_RELEASE} | cut -c2-)"
CALIBRE_URL="https://download.calibre-ebook.com/${CALIBRE_VERSION}/calibre-${CALIBRE_VERSION}-x86_64.txz"

mkdir -p "$CALIBRE_DEST"
curl -o /tmp/calibre-tarball.txz -L "$CALIBRE_URL"
tar xvf /tmp/calibre-tarball.txz -C "$CALIBRE_DEST"
