#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BOOK_DIR="$(realpath "${1:?usage: build_book.sh <book-directory>}")"
BUILD_ENV="$(mktemp -d "${TMPDIR:-/tmp}/neurodesk-book.XXXXXX")"
trap 'rm -rf "$BUILD_ENV"' EXIT

# Keep the book builder separate from Neurodesktop's Python packages and pip config.
python3 -m venv "$BUILD_ENV"
"$BUILD_ENV/bin/python" --version
"$BUILD_ENV/bin/python" -m pip --version
PIP_CONFIG_FILE=/dev/null "$BUILD_ENV/bin/python" -m pip --isolated install \
    --index-url https://pypi.org/simple --retries 5 --timeout 60 \
    -r "$SCRIPT_DIR/book-requirements.txt"
"$BUILD_ENV/bin/python" -m pip check
"$BUILD_ENV/bin/jupyter-book" --version

cd "$BOOK_DIR"
bash "$SCRIPT_DIR/write-toc-entry.sh"
# The notebooks have already run in the execution jobs.
sed -i 's/execute_notebooks: .*/execute_notebooks: off/' _config.yml
"$BUILD_ENV/bin/jupyter-book" build .
