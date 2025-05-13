#!/bin/bash

set -euo pipefail

usage() {
  echo "Usage: $0 -r <repository> -v <version> -p <pattern> -s <sha256> [-o <output_dir>]"
  echo "  -r  Repository in the format owner/repo (e.g., aquasecurity/trivy)"
  echo "  -v  Version of the release (e.g., v1.0.0)"
  echo "  -p  Artifact pattern to match (e.g., artifact_name_*.tar.gz)"
  echo "  -s  Expected SHA256 checksum of the artifact"
  echo "  -o  Output directory to store the downloaded artifact (optional, defaults to a temporary directory)"
  exit 1
}

REPO=""
VERSION=""
PATTERN=""
SHA256=""
OUTPUT_DIR=$(mktemp -d)

while getopts "r:v:p:s:o:" opt; do
  case "$opt" in
    r) REPO="$OPTARG" ;;
    v) VERSION="$OPTARG" ;;
    p) PATTERN="$OPTARG" ;;
    s) SHA256="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    *) usage ;;
  esac
done

if [[ -z "$REPO" || -z "$VERSION" || -z "$PATTERN" || -z "$SHA256" ]]; then
  usage
fi

echo "::group::Downloading release asset"
gh release download "$VERSION" \
  --repo "$REPO" \
  --pattern "$PATTERN" \
  --dir "$OUTPUT_DIR" \
  --skip-existing

TARBALL=$(find "$OUTPUT_DIR" -name "$PATTERN")
if [ -z "$TARBALL" ]; then
  echo "::error::Failed to download release asset."
  exit 1
fi
echo "Downloaded artifact: $TARBALL"
echo "::endgroup::"

echo "::group::Verifying checksum"
if ! echo "${SHA256}  ${TARBALL}" | sha256sum -c --status --strict -; then
  echo "::error::Checksum verification failed! The downloaded file does not match the expected SHA256 checksum."
  exit 1
fi
echo "Checksum verification passed."
echo "::endgroup::"

echo "Downloaded and verified artifact is located at: $TARBALL"
