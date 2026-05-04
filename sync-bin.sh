#!/usr/bin/env bash
set -euo pipefail

# Override these if your SSH names differ:
#   FALCON_SSH=eric@falcon ./sync-binaries.sh
#   ACROBAT_SSH=dev@acrobat.home.arpa ./sync-binaries.sh
FALCON_SSH="${FALCON_SSH:-dev@falcon}"
ACROBAT_SSH="${ACROBAT_SSH:-dev@acrobat.home.arpa}"

FALCON_ROOT="/mnt/dev/Local/Code/gem5/Final/binaries"
ACROBAT_ROOT="/home/dev/Local_Code/BCM2712_GEM5/binaries"

FILES=(
    "GEMM/gemm-native"
    "GEMM/gemm-arm"
    "GEMM/gemm-x86"
    "FFT/fft-native"
    "FFT/fft-arm"
    "FFT/fft-x86"
)

mode="to"   # default: send from current machine to the other

usage() {
    cat <<EOF
Usage: $0 [-t | -f]

Options:
  -t    Send binaries from this machine to the other machine. Default.
  -f    Fetch binaries from the other machine to this machine.

Environment overrides:
  FALCON_SSH      SSH target for Falcon.  Default: falcon
  ACROBAT_SSH     SSH target for Acrobat. Default: dev@acrobat.home.arpa
EOF
}

while getopts ":tfh" opt; do
    case "$opt" in
        t) mode="to" ;;
        f) mode="from" ;;
        h)
            usage
            exit 0
            ;;
        *)
            usage
            exit 1
            ;;
    esac
done

host="$(hostname -s | tr '[:upper:]' '[:lower:]')"

case "$host" in
    falcon*)
        local_root="$FALCON_ROOT"
        remote_root="$ACROBAT_ROOT"
        remote_host="$ACROBAT_SSH"
        local_name="falcon"
        remote_name="acrobat"
        ;;
    acrobat*)
        local_root="$ACROBAT_ROOT"
        remote_root="$FALCON_ROOT"
        remote_host="$FALCON_SSH"
        local_name="acrobat"
        remote_name="falcon"
        ;;
    *)
        echo "Error: this script only knows how to run from falcon or acrobat."
        echo "Detected hostname: $host"
        exit 1
        ;;
esac

send_file() {
    local rel="$1"
    local src="$local_root/$rel"
    local dst="$remote_root/$rel"
    local dst_dir
    dst_dir="$(dirname "$dst")"

    if [[ ! -f "$src" ]]; then
        echo "Skipping missing local file: $src"
        return
    fi

    echo "Sending $rel: $local_name -> $remote_name"
    ssh "$remote_host" "mkdir -p '$dst_dir'"
    rsync -av "$src" "$remote_host:$dst"
}

fetch_file() {
    local rel="$1"
    local src="$remote_root/$rel"
    local dst="$local_root/$rel"
    local dst_dir
    dst_dir="$(dirname "$dst")"

    if ! ssh "$remote_host" "test -f '$src'"; then
        echo "Skipping missing remote file: $remote_host:$src"
        return
    fi

    echo "Fetching $rel: $remote_name -> $local_name"
    mkdir -p "$dst_dir"
    rsync -av "$remote_host:$src" "$dst"
}

echo "Running on: $local_name"
echo "Mode: $mode"

if [[ "$mode" == "to" ]]; then
    for rel in "${FILES[@]}"; do
        send_file "$rel"
    done
else
    for rel in "${FILES[@]}"; do
        fetch_file "$rel"
    done
fi