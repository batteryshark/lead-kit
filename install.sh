#!/usr/bin/env bash
# Standalone Lead kit. Requires --lead-config FILE; no Chief, routing or services.
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mode=install; config=""; hosts=()
while (($#)); do
  case "$1" in
    --lead-config) shift; config="${1:?--lead-config requires JSON}" ;;
    --print) mode=print ;; --dry-run) mode=dry ;; --uninstall) mode=uninstall ;;
    opencode|claude|codex) hosts+=("$1") ;;
    -h|--help) echo 'install.sh --lead-config FILE [--print|--dry-run|--uninstall] [opencode claude codex]'; exit 0 ;;
    *) echo "unsupported argument: $1" >&2; exit 2 ;;
  esac
  shift
done
[[ -n $config ]] || { echo '--lead-config required' >&2; exit 2; }
((${#hosts[@]})) || hosts=(opencode claude codex)
exec python3 "$SRC/scripts/install-lead.py" "$config" "$mode" "${hosts[@]}"
