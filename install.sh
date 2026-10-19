#!/usr/bin/env bash
# Hosts and packs are explicit in the config.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mode=install; config=""
while (($#)); do
  case "$1" in
    --lead-config) shift; config="${1:?--lead-config requires JSON}" ;;
    --print) mode=print ;; --dry-run) mode=dry ;; --uninstall) mode=uninstall ;;
    --list-packs) exec python3 "$SRC/scripts/install-lead.py" --list-packs ;;
    opencode|claude|codex) echo 'Set hosts explicitly in config v2; positional host arguments are no longer accepted.' >&2; exit 2 ;;
    -h|--help) echo 'install.sh --list-packs | --lead-config FILE [--print|--dry-run|--uninstall]'; exit 0 ;;
    *) echo "unsupported argument: $1" >&2; exit 2 ;;
  esac
  shift
done
[[ -n $config ]] || { echo '--lead-config required' >&2; exit 2; }
exec python3 "$SRC/scripts/install-lead.py" "$config" "$mode"
