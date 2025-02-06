#!/bin/bash

mount -o rw,remount /
setenforce 0

# Default to relative path, but allow override via environment variable. Helpful for dev vs prod env
VISIONAI_PATH="${VISIONAI_PATH_OVERRIDE:-./visionai.py}"

export XDG_RUNTIME_DIR=/dev/socket/weston
export WAYLAND_DISPLAY=wayland-1

exec "$VISIONAI_PATH"
