#!/usr/bin/env bash

# Wrapper to execute the uninstall path in install.sh

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -f "$SCRIPT_DIR/install.sh" ]; then
    bash "$SCRIPT_DIR/install.sh" --uninstall
else
    echo "Error: install.sh not found in $SCRIPT_DIR"
    exit 1
fi
