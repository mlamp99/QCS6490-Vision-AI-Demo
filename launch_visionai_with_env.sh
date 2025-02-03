#!/bin/bash

mount -o rw,remount /
setenforce 0

export XDG_RUNTIME_DIR=/dev/socket/weston
export WAYLAND_DISPLAY=wayland-1

export CAM1=/dev/video0
export CAM2=""

./visionai.py
