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
    DEFAULT_DUAL_WINDOW,
    DEFAULT_LEFT_WINDOW,
    DEPTH_SEGMENTATION,
    OBJECT_DETECTION,
    POSE_DETECTION,
    SEGMENTATION,
)

# Locks app version, prevents warnings
gi.require_version("Gtk", "3.0")

from gi.repository import GLib, Gtk

# Tuning variable to adjust the height of the video display
HEIGHT_OFFSET = 17


class Handler:
    def __init__(self, display_fps_metrics=True):
        self.demoList = [
            None,
            CAMERA,
            POSE_DETECTION,
            SEGMENTATION,
            CLASSIFICATION,
            OBJECT_DETECTION,
            DEPTH_SEGMENTATION,
        ]
        self.demoProcess0 = None
        self.demoProcess1 = None
        self.QProf = None
        self.frame0 = None
        self.frame1 = None
        # These values should be determined by GUI's allocation (IE glade's config)
        self.allocated_sizes = False
        self.DrawArea1_x = None
        self.DrawArea1_y = None
        self.DrawArea1_w = None
        self.DrawArea1_h = None
        self.DrawArea2_x = None
        self.DrawArea2_y = None
        self.DrawArea2_w = None
        self.DrawArea2_h = None
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

    def _modify_command_pipeline(self, command, stream_index):

        # TODO: support l/r windows through parameterization or other technique
        displaysink_text = (
            "fpsdisplaysink text-overlay=true video-sink="
            if self.display_fps_metrics
            else ""
        )

        # NOTE: if fpsdisplaysink is used, the video-sink property needs wrapped; "" does that
        command = command.replace(
            "<SINGLE_DISPLAY>",
            f'{displaysink_text}"{DEFAULT_LEFT_WINDOW}"',
        )
        command = command.replace(
            "<DUAL_DISPLAY>",
            f'{displaysink_text}"{DEFAULT_DUAL_WINDOW}"',
        )

        # TODO: If we do file processing, we'll need to support that around here
        command = command.replace(
            "<DATA_SRC>",
            f"v4l2src device={self.cam1 if stream_index == 0 else self.cam2}",
        )
        if stream_index == 0:
            # TODO: remove these nasty position replacements with something more obvious
            command = command.replace(
                "x=10 y=50 width=640 height=480",
                f"x={self.DrawArea1_x} y={self.DrawArea1_y} width={self.DrawArea1_w} height={self.DrawArea1_h}",
            )
            # TODO: if dual window is enabled, we need to terminate other window
            command = command.replace(
                "<DUAL_WINDOW_XY>",
                f"x={self.DrawArea1_x} y={self.DrawArea1_y} width={2*self.DrawArea1_w} height={self.DrawArea1_h}",
            )
        else:
            command = command.replace(
                "x=10 y=50 width=640 height=480",
                f"x={self.DrawArea2_x} y={self.DrawArea2_y} width={self.DrawArea2_w} height={self.DrawArea2_h}",
            )
        return command

    def update_window_allocations(self):
        """Dynamically determine the size and position of the video windows based on the current GUI partitioning."""
        if not self.allocated_sizes:
            # TODO: Pull up allocation/sizing to previous function closer to init
            self.update_window_allocations()
            allocation = self.DrawArea1.get_allocation()
            self.DrawArea1_x = allocation.x
            self.DrawArea1_y = allocation.y + HEIGHT_OFFSET
            self.DrawArea1_w = allocation.width
            self.DrawArea1_h = allocation.height + HEIGHT_OFFSET

            allocation = self.DrawArea2.get_allocation()
            self.DrawArea2_x = allocation.x
            self.DrawArea2_y = allocation.y + HEIGHT_OFFSET
            self.DrawArea2_w = allocation.width
            self.DrawArea2_h = allocation.height + HEIGHT_OFFSET

            self.allocated_sizes = True

    def getCommand(self, demoIndex, streamIndex):
        self.update_window_allocations()
        command = self.demoList[demoIndex][:]
        command = self._modify_command_pipeline(command)

        print(command)
        print((self.DrawArea1_x, self.DrawArea1_y, self.DrawArea1_w, self.DrawArea1_h))
        print((self.DrawArea2_x, self.DrawArea2_y, self.DrawArea2_w, self.DrawArea2_h))
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
