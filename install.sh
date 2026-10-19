#!/usr/bin/env bash
# Presets use stable shipped config paths so all modes share installation identity.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mode=install; config=""; selection=""; mode_set=""; list=""
fail() { echo "install.sh: $*" >&2; exit 2; }
while (($#)); do
  case "$1" in
    --preset|--lead-config)
      [[ -z $selection ]] || fail 'choose exactly one --preset or --lead-config'
      selection="$1"; shift
      [[ $# -gt 0 && $1 != --* && -n $1 ]] || fail "$selection requires a value"
      if [[ $selection == --preset ]]; then
        case "$1" in
          opencode|claude|codex|pi) config="$SRC/presets/$1.json" ;;
          *) fail 'unknown preset; choose opencode, claude, codex or pi' ;;
        esac
      else config="$1"; fi ;;
    --print|--dry-run|--uninstall)
      [[ -z $mode_set ]] || fail 'choose only one of --print, --dry-run or --uninstall'
      mode_set="$1"
      case "$1" in --print) mode=print ;; --dry-run) mode=dry ;; --uninstall) mode=uninstall ;; esac ;;
    --list-packs) [[ -z $list ]] || fail 'duplicate --list-packs'; list=1 ;;
    opencode|claude|codex|pi) fail 'use --preset HOST or set hosts in --lead-config FILE' ;;
    -h|--help)
      echo 'install.sh (--preset HOST | --lead-config FILE) [--print|--dry-run|--uninstall]'
      echo 'HOST: opencode, claude, codex, pi. Presets install project-lead with engineering practice.'
      echo 'install.sh --list-packs (shows host applicability and prerequisites)'
      exit 0 ;;
    *) echo "unsupported argument: $1" >&2; exit 2 ;;
  esac
  shift
done
if [[ -n $list ]]; then
  [[ -z $selection && -z $mode_set ]] || fail '--list-packs must be used alone'
  exec python3 "$SRC/scripts/install-lead.py" --list-packs
fi
[[ -n $config ]] || fail 'choose --preset HOST or --lead-config FILE'
exec python3 "$SRC/scripts/install-lead.py" "$config" "$mode"
