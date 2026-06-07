#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LAUNCH_SCRIPT="${PROJECT_ROOT}/scripts/launch_macos.sh"
DESTINATION="${1:-${HOME}/Desktop/凤梨罐头 FILM LAB.app}"

if [[ ! -x "${LAUNCH_SCRIPT}" ]]; then
  printf '启动脚本不可执行：%s\n' "${LAUNCH_SCRIPT}"
  exit 1
fi

rm -rf "${DESTINATION}"
osacompile \
  -o "${DESTINATION}" \
  -e 'on run' \
  -e 'try' \
  -e "do shell script quoted form of \"${LAUNCH_SCRIPT}\"" \
  -e 'on error errorMessage number errorNumber' \
  -e 'display alert "无法启动凤梨罐头 FILM LAB" message errorMessage as critical' \
  -e 'end try' \
  -e 'end run'

printf '桌面启动器已创建：%s\n' "${DESTINATION}"
