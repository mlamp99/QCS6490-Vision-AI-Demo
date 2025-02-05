#!/bin/bash

mount -o rw,remount /
setenforce 0

export XDG_RUNTIME_DIR=/dev/socket/weston
export WAYLAND_DISPLAY=wayland-1

#TODO: Delete when camera auto selection is implemented
export CAM1=/dev/video2
export CAM2=/dev/video4

./visionai.py
