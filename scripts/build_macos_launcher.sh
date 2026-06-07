#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LAUNCH_SCRIPT="${PROJECT_ROOT}/scripts/launch_macos.sh"
ICON_FILE="${PROJECT_ROOT}/assets/macos/camera-icon.icns"
PROJECT_DESTINATION="${PROJECT_ROOT}/launcher/凤梨罐头 FILM LAB.app"
DESKTOP_DESTINATION="${HOME}/Desktop/凤梨罐头 FILM LAB.app"
PLIST_BUDDY="/usr/libexec/PlistBuddy"

if [[ ! -x "${LAUNCH_SCRIPT}" ]]; then
  printf '启动脚本不可执行：%s\n' "${LAUNCH_SCRIPT}"
  exit 1
fi

if [[ ! -f "${ICON_FILE}" ]]; then
  printf '应用图标不存在：%s\n' "${ICON_FILE}"
  exit 1
fi

build_launcher() {
  local destination="$1"
  local mode="$2"

  mkdir -p "$(dirname "${destination}")"
  rm -rf "${destination}"
  if [[ "${mode}" == "relative" ]]; then
    osacompile \
      -o "${destination}" \
      -e 'on run' \
      -e 'try' \
      -e 'set appPath to POSIX path of (path to me)' \
      -e 'set projectRoot to do shell script "cd " & quoted form of (appPath & "../..") & " && pwd"' \
      -e 'do shell script quoted form of (projectRoot & "/scripts/launch_macos.sh")' \
      -e 'on error errorMessage number errorNumber' \
      -e 'display alert "无法启动凤梨罐头 FILM LAB" message errorMessage as critical' \
      -e 'end try' \
      -e 'end run'
  else
    osacompile \
      -o "${destination}" \
      -e 'on run' \
      -e 'try' \
      -e "do shell script quoted form of \"${LAUNCH_SCRIPT}\"" \
      -e 'on error errorMessage number errorNumber' \
      -e 'display alert "无法启动凤梨罐头 FILM LAB" message errorMessage as critical' \
      -e 'end try' \
      -e 'end run'
  fi

  rm -f \
    "${destination}/Contents/Resources/Assets.car" \
    "${destination}/Contents/Resources/applet.icns"
  cp "${ICON_FILE}" "${destination}/Contents/Resources/camera-icon.icns"
  "${PLIST_BUDDY}" -c "Delete :CFBundleIconName" \
    "${destination}/Contents/Info.plist" 2>/dev/null || true
  "${PLIST_BUDDY}" -c "Set :CFBundleIconFile camera-icon.icns" \
    "${destination}/Contents/Info.plist"
  "${PLIST_BUDDY}" -c "Add :CFBundleIdentifier string com.yuanzhi0419.pineapple-film-lab" \
    "${destination}/Contents/Info.plist"
  "${PLIST_BUDDY}" -c "Add :CFBundleVersion string 1" \
    "${destination}/Contents/Info.plist"
  "${PLIST_BUDDY}" -c "Add :CFBundleShortVersionString string 0.1.0" \
    "${destination}/Contents/Info.plist"
  touch "${destination}"
  xattr -cr "${destination}"
  if ! codesign --force --deep --sign - "${destination}" >/dev/null 2>&1; then
    xattr -cr "${destination}"
    codesign --force --deep --sign - "${destination}" >/dev/null
  fi
  xattr -cr "${destination}"
  printf '快捷启动器已创建：%s\n' "${destination}"
}

if [[ $# -gt 0 ]]; then
  build_launcher "$1" "fixed"
else
  build_launcher "${PROJECT_DESTINATION}" "relative"
  build_launcher "${DESKTOP_DESTINATION}" "fixed"
fi
