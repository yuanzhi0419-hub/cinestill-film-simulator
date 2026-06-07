#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PINEAPPLE_FILM_LAB_PORT:-7860}"
URL="http://127.0.0.1:${PORT}"
LOG_DIR="${HOME}/Library/Logs/PineappleFilmLab"
LOG_FILE="${LOG_DIR}/server.log"
PID_FILE="${LOG_DIR}/server.pid"

open_app() {
  if [[ "${PINEAPPLE_FILM_LAB_NO_OPEN:-0}" != "1" ]]; then
    open "${URL}"
  fi
}

if curl --fail --silent --show-error "${URL}/api/health" >/dev/null 2>&1; then
  open_app
  exit 0
fi

GUNICORN="${PROJECT_ROOT}/.venv/bin/gunicorn"
if [[ ! -x "${GUNICORN}" ]]; then
  printf '%s\n' \
    "项目运行环境不存在。" \
    "请先按照 README.md 完成依赖安装：" \
    "${PROJECT_ROOT}"
  exit 1
fi

mkdir -p "${LOG_DIR}"
cd "${PROJECT_ROOT}"

nohup "${GUNICORN}" \
  --bind "127.0.0.1:${PORT}" \
  --workers 1 \
  --threads 4 \
  run:app \
  >"${LOG_FILE}" 2>&1 < /dev/null &
echo "$!" >"${PID_FILE}"

for _ in {1..40}; do
  if curl --fail --silent --show-error "${URL}/api/health" >/dev/null 2>&1; then
    open_app
    exit 0
  fi
  sleep 0.25
done

printf '%s\n' \
  "本地服务启动失败。" \
  "请检查日志：${LOG_FILE}"
exit 1
