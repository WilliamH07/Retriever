#!/bin/sh
# Active les hooks versionnés du dépôt (à lancer une fois après le clone).
set -eu
cd "$(git rev-parse --show-toplevel)"
chmod +x .githooks/* scripts/secret_scan.py
git config core.hooksPath .githooks
echo "Hooks activés : chaque commit est maintenant analysé (secrets)."
command -v gitleaks >/dev/null 2>&1 || echo "Conseil : brew install gitleaks (contrôle renforcé)."
