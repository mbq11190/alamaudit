#!/usr/bin/env bash
set -euo pipefail
HOOK=.git/hooks/pre-commit
cat > "$HOOK" <<'HOOK'
#!/usr/bin/env bash
# Prevent committing Python/manifest files with disallowed Unicode bullets or smart quotes
ROOT=$(git rev-parse --show-toplevel)
python3 "$ROOT/scripts/check_no_unicode_bullets.py" "$ROOT"
HOOK
chmod +x "$HOOK"
echo "Installed pre-commit hook to run scripts/check_no_unicode_bullets.py"
