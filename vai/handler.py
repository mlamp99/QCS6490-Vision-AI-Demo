import os
import signal
import sys
from time import sleep

import cairo
import cv2
import gi
import psutil

from .cam import camThread
from .common import (
    APP_NAME,
    CAMERA,
    CLASSIFICATION,
    DEFAULT_DISPLAY,
    OBJECT_DETECTION,
    POSE_DETECTION,
    SEGMENTATION,
)

# Locks app version, prevents warnings
gi.require_version("Gtk", "3.0")

from gi.repository import GLib, Gtk


class Handler:
    def __init__(self, display_fps_metrics=True):
        self.demoList = [
            None,
            CAMERA,
            POSE_DETECTION,
            SEGMENTATION,
            CLASSIFICATION,
            OBJECT_DETECTION,
        ]
        self.demoProcess0 = None
        self.demoProcess1 = None
        self.QProf = None
        self.frame0 = None
        self.frame1 = None
        self.DrawArea1_x = 0
        self.DrawArea1_y = 0
        self.DrawArea1_w = 640
        self.DrawArea1_h = 480
        self.display_fps_metrics = display_fps_metrics

        print(
            "Pulling CAM1 and CAM2 from ENV; defaulting to /dev/video0 and /dev/video1 if not set."
        )
        self.cam1 = os.environ.get("CAM1", "/dev/video0")
        self.cam2 = os.environ.get("CAM2", "/dev/video1")
        print(f"Using CAM1: {self.cam1} and CAM2: {self.cam2}")

        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, self.exit, "SIGINT")
        # GObject.timeout_add(100,  self.UpdateLoads)
        # GObject.timeout_add(2000, self.UpdateTemp)

    def exit(self, payload):
        """Handle exit signals and clean up resources before exiting the application.

        Due to the threaded nature of the application, this function needs to be carefully linked with Gtk
        """

        exit_message = f"Exiting {APP_NAME}" + (f" due to {payload}" if payload else "")
        print(f"\n{exit_message}")

        Gtk.main_quit()
        # Unclear if Max meant to register the mainWindow destroy function,
        # but it doesn't appear to be registered right now so call it manually
        self.on_mainWindow_destroy()

        sys.exit(0)

    def UpdateLoads(self):
        GLib.idle_add(
            self.IdleUpdateLabels,
            self.CPU_load,
            "{:.2f}".format(self.QProf.GetCPU(), 2),
        )
        GLib.idle_add(
            self.IdleUpdateLabels,
            self.GPU_load,
            "{:.2f}".format(self.QProf.GetGPU(), 2),
        )
        GLib.idle_add(
            self.IdleUpdateLabels,
            self.MEM_load,
            "{:.2f}".format(self.QProf.GetMEM(), 2),
        )
        return True

    def UpdateTemp(self):
        temps = psutil.sensors_temperatures()
        if temps:
            cpuTemp = 0
            gpuTemp = 0
            memTemp = 0
            for name, entries in temps.items():
                for entry in entries:
                    if name == "cpu0_thermal":
                        cpuTemp = cpuTemp + entry.current
                    elif name == "cpu1_thermal":
                        cpuTemp = cpuTemp + entry.current
                    elif name == "cpu2_thermal":
                        cpuTemp = cpuTemp + entry.current
                    elif name == "cpu3_thermal":
                        cpuTemp = cpuTemp + entry.current
                    elif name == "cpu4_thermal":
                        cpuTemp = cpuTemp + entry.current
                    elif name == "cpu5_thermal":
                        cpuTemp = cpuTemp + entry.current
                    elif name == "cpu6_thermal":
                        cpuTemp = cpuTemp + entry.current
                    elif name == "cpu7_thermal":
                        cpuTemp = cpuTemp + entry.current
                    elif name == "cpu8_thermal":
                        cpuTemp = cpuTemp + entry.current
                    elif name == "cpu9_thermal":
                        cpuTemp = cpuTemp + entry.current
                    elif name == "cpu10_thermal":
                        cpuTemp = cpuTemp + entry.current
                    elif name == "cpu11_thermal":
                        cpuTemp = cpuTemp + entry.current
                    elif name == "ddr_thermal":
                        memTemp = entry.current
                    elif name == "video_thermal":
                        gpuTemp = entry.current

            GLib.idle_add(
                self.IdleUpdateLabels, self.CPU_temp, "{:.2f}".format(cpuTemp / 12, 2)
            )
            GLib.idle_add(
                self.IdleUpdateLabels, self.GPU_temp, "{:.2f}".format(gpuTemp, 2)
            )
            GLib.idle_add(
                self.IdleUpdateLabels, self.MEM_temp, "{:.2f}".format(memTemp, 2)
            )
        return True

    def close_about(self, *args):
        self.aboutWindow.hide()

    def open_about(self, *args):
        self.aboutWindow.set_transient_for(self.MainWindow)
        self.aboutWindow.run()

    def on_mainWindow_destroy(self, *args):
        if self.QProf is not None:
            self.QProf.Close()

        if self.demoProcess0 is not None:
            self.demoProcess0.close()

        if self.demoProcess1 is not None:
            self.demoProcess1.close()

        Gtk.main_quit(*args)

    def _modify_command_pipeline(self, command):
        if self.display_fps_metrics:
            command = command.replace(
                "<DISPLAY>",
                f'fpsdisplaysink text-overlay=true video-sink="{DEFAULT_DISPLAY}"',
            )
        else:
            command = command.replace(
                "<DISPLAY>",
                DEFAULT_DISPLAY,
            )
        return command

    def getCommand(self, demoIndex, streamIndex):
        allocation = self.DrawArea1.get_allocation()
        self.DrawArea1_x = allocation.x
        self.DrawArea1_y = allocation.y
        self.DrawArea1_w = allocation.width
        self.DrawArea1_h = allocation.height

        command = self.demoList[demoIndex][:]
        command = self._modify_command_pipeline(command)

        if streamIndex == 0:
            allocation = self.DrawArea1.get_allocation()
            self.DrawArea1_x = allocation.x
            self.DrawArea1_y = allocation.y + 17
            self.DrawArea1_w = allocation.width
            self.DrawArea1_h = allocation.height + 18

            # command = command.replace('<DATA_SRC>', 'camera=0')
            command = command.replace("<DATA_SRC>", f"v4l2src device={self.cam1}")
            command = command.replace(
                "x=10 y=50 width=640 height=480",
                f"x={self.DrawArea1_x} y={self.DrawArea1_y} width={self.DrawArea1_w} height={self.DrawArea1_h}",
            )
        else:
            command = command.replace("<DATA_SRC>", "camera=1")

        return command

    def demo0_selection_changed_cb(self, combo):
        if self.demoProcess0 is not None:
            # end previous process
            self.demoProcess0.close()
            sleep(1)

        index = combo.get_active()
        if index == 0:
            self.demoProcess0 = None
        else:
            self.demoProcess0 = camThread(self.getCommand(index, 0))
            self.demoProcess0.start()

    def demo1_selection_changed_cb(self, combo):
        if self.demoProcess1 is not None:
            # end previous process
            self.demoProcess1.close()
            sleep(1)

        index = combo.get_active()
        if index == 0:
            self.demoProcess1 = None
        else:
            self.demoProcess1 = camThread(self.getCommand(index, 1))
            self.demoProcess1.start()

    def IdleUpdateLabels(self, label, text):
        label.set_text(text)

    def CapImage_event1(self, widget, context):
        try:
            if self.demoProcess0.frame_available():
                self.frame0 = self.demoProcess0.frame()

                self.frame0 = cv2.cvtColor(self.frame0[:, :, ::-1], cv2.COLOR_BGR2RGBA)
                H, W, C = self.frame0.shape

                # {.. insert code to modify alpha channel here..}
                surface = cairo.ImageSurface.create_for_data(
                    self.frame0, cairo.FORMAT_ARGB32, W, H
                )

                # surface = cairo.ImageSurface.create_for_data(self.frame0, cairo.FORMAT_ARGB32, W, H)
                CWidth = widget.get_allocation().width
                CHeight = widget.get_allocation().height

                if CHeight / H < CWidth / W:
                    frameScale = CHeight / H
                else:
                    frameScale = CWidth / W

                context.scale(frameScale, frameScale)
                context.set_source_surface(
                    surface,
                    ((CWidth / frameScale) - W) / 2,
                    ((CHeight / frameScale) - H) / 2,
                )
                context.paint()
            GLib.idle_add(
                self.IdleUpdateLabels,
                self.FPSRate0,
                str(self.demoProcess0.FPSAvarage()),
            )
        except:
            GLib.idle_add(self.IdleUpdateLabels, self.FPSRate0, "0")
            pass
        widget.queue_draw()

    def CapImage_event2(self, widget, context):
        try:
            if self.demoProcess1.frame_available():
                self.frame1 = self.demoProcess1.frame()
                H, W, C = self.frame1.shape
                surface = cairo.ImageSurface.create_for_data(
                    self.frame1, cairo.FORMAT_ARGB32, W, H
                )
                CWidth = widget.get_allocation().width
                CHeight = widget.get_allocation().height

                if CHeight / H < CWidth / W:
                    frameScale = CHeight / H
                else:
                    frameScale = CWidth / W

                context.scale(frameScale, frameScale)
                context.set_source_surface(
                    surface,
                    ((CWidth / frameScale) - W) / 2,
                    ((CHeight / frameScale) - H) / 2,
                )
                context.paint()
            GLib.idle_add(
                self.IdleUpdateLabels,
                self.FPSRate1,
                str(self.demoProcess1.FPSAvarage()),
            )
        except:
            GLib.idle_add(self.IdleUpdateLabels, self.FPSRate1, "0")
            pass
        widget.queue_draw()
