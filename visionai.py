#!/usr/bin/env python3

import math
import os
import threading
import time

import gi

from vai.common import (
    APP_HEADER,
    GRAPH_SAMPLE_SIZE,
    TRIA,
    TRIA_BLUE_RGBH,
    TRIA_PINK_RGBH,
    TRIA_YELLOW_RGBH,
    GRAPH_DRAW_PERIOD_ms,
)
from vai.handler import Handler
from vai.qprofile import QProfProcess

# os.environ["XDG_RUNTIME_DIR"] = "/dev/socket/weston"
# os.environ["WAYLAND_DISPLAY"] = "wayland-1"
# os.environ["GDK_BACKEND"] = "wayland"
# os.environ["LC_ALL"] = "en.utf-8"

# os.environ["QMONITOR_BACKEND_LIB_PATH"] = "/var/QualcommProfiler/libs/backends/"
# os.environ["LD_LIBRARY_PATH"] = "$LD_LIBRARY_PATH:/var/QualcommProfiler/libs/"
# os.environ["PATH"] = "$PATH:/data/shared/QualcommProfiler/bins"

# Locks app version, prevents warnings
gi.require_version("Gdk", "3.0")
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, Gst, Gtk

CPU_UTIL_KEY = "cpu %"
MEM_UTIL_KEY = "lpddr5 %"
GPU_UTIL_KEY = "gpu %"
CPU_THERMAL_KEY = "cpu temp (°c)"
MEM_THERMAL_KEY = "lpddr5 temp (°c)"
GPU_THERMAL_KEY = "gpu temp (°c)"

UTIL_GRAPH_COLORS_RGBF = {
    CPU_UTIL_KEY: tuple(c / 255.0 for c in TRIA_PINK_RGBH),
    MEM_UTIL_KEY: tuple(c / 255.0 for c in TRIA_BLUE_RGBH),
    GPU_UTIL_KEY: tuple(c / 255.0 for c in TRIA_YELLOW_RGBH),
}

THERMAL_GRAPH_COLORS_RGBF = {
    CPU_THERMAL_KEY: tuple(c / 255.0 for c in TRIA_PINK_RGBH),
    MEM_THERMAL_KEY: tuple(c / 255.0 for c in TRIA_BLUE_RGBH),
    GPU_THERMAL_KEY: tuple(c / 255.0 for c in TRIA_YELLOW_RGBH),
}

GladeBuilder = Gtk.Builder()
APP_FOLDER = os.path.dirname(__file__)
RESOURCE_FOLDER = os.path.join(APP_FOLDER, "resources")
LAYOUT_PATH = os.path.join(RESOURCE_FOLDER, "GSTLauncher.glade")


def lerp(a, b, t):
    """Linear interpolation between two values"""
    return a + t * (b - a)


def draw_graph_background_and_border(width, height, cr):
    cr.set_source_rgba(0.1, 0.1, 0.1, 0.15)  # Transparent gray container fill
    cr.rectangle(0, 0, width, height)
    cr.fill_preserve()
    cr.set_source_rgb(0.5, 0.5, 0.5)  # Gray border
    cr.set_line_width(2)
    cr.stroke()


def draw_graph_legend(label_color_map, width, cr, legend_x_width=None):
    """
    Draw the legend for the graph, returning the x position of the legend

    Args:
        label_color_map: Dict of label to RGB color tuple
        width: Width of the graph area
        cr: Cairo context
        legend_x_width: Width of the legend box. If None, the width is determined by the labels
    """
    # --- Draw Legend ---
    # TODO: Scale by res?
    legend_margin_x = 20  # Distance from the right edge
    legend_margin_y = 10  # Distance from the top edge
    box_size = 20  # Size of the color box
    spacing = 30  # Vertical spacing between entries
    legend_padding_x = 5

    cr.select_font_face("Sans", 0, 1)  # Bold weight & normal slant
    cr.set_font_size(20)

    text_guess_width = 11 * max(len(label) for label, _ in label_color_map.items())
    legend_x = (
        width - legend_x_width
        if legend_x_width
        else width - legend_margin_x - text_guess_width - box_size
    )

    # Tuning offset variable
    for i, (label, color) in enumerate(label_color_map.items()):
        item_y = legend_margin_y + i * spacing

        # Draw color box
        cr.set_source_rgb(*color)
        cr.rectangle(legend_x, item_y, box_size, box_size)
        cr.fill()

        # Draw label text in white
        cr.set_source_rgb(1, 1, 1)
        text_x = legend_x + box_size + legend_padding_x
        text_y = (
            item_y + box_size - 5
        )  # Shift text slightly so it's vertically centered
        cr.move_to(text_x, text_y)
        cr.show_text(label.upper())

    return legend_x


def draw_graph_data(data_map, data_color_map, width, height, cr, y_lim=(0, 100)):
    """Draw the graph data on the draw area with the given colors

    Args:
        data_map: Dict of data key to list of data values
        data_color_map: Dict of data key to RGB color tuple
        width: Width of the graph area
        height: Height of the graph area
        cr: Cairo context
        y_lim (optional): Tuple of min and max y values
    """

    # --- Draw line graph ---
    # TODO: Scale by res?
    cr.set_line_width(2)

    # TODO: simply draw the sampled data where data_color_zip[0][0] is the y value for x=0.
    for data_key, data in data_map.items():
        cr.set_source_rgb(*data_color_map[data_key])
        cr.move_to(0, int(lerp(y_lim[0], height, 1 - data[0] / y_lim[1])))
        for x in range(1, len(data)):
            cr.line_to(
                int(lerp(0, width, x / len(data))),
                int(lerp(y_lim[0], height, 1 - data[x] / y_lim[1])),
            )
        cr.stroke()


class VaiDemoManager:
    def __init__(self, port=7001):
        Gst.init(None)

        self.eventHandler = Handler()
        self.running = True

        self.localAppThread = threading.Thread(target=self.localApp)
        self.localAppThread.start()

    def init_graph_data(self, sample_size=GRAPH_SAMPLE_SIZE):
        """Initialize the graph data according to graph box size"""
        self.util_data = {
            CPU_UTIL_KEY: [0] * sample_size,
            MEM_UTIL_KEY: [0] * sample_size,
            GPU_UTIL_KEY: [0] * sample_size,
        }
        self.thermal_data = {
            CPU_THERMAL_KEY: [0] * sample_size,
            MEM_THERMAL_KEY: [0] * sample_size,
            GPU_THERMAL_KEY: [0] * sample_size,
        }

    def on_util_graph_draw(self, widget, cr):
        """Draw the graph on the draw area"""

        if self.util_data is None or self.thermal_data is None:
            self.init_graph_data()

        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        draw_graph_background_and_border(width, height, cr)
        legend_x = draw_graph_legend(UTIL_GRAPH_COLORS_RGBF, width, cr, 220)
        draw_graph_data(
            self.util_data,
            UTIL_GRAPH_COLORS_RGBF,
            legend_x,
            height,
            cr,
            y_lim=(0, 100),
        )

    def on_thermal_graph_draw(self, widget, cr):
        """Draw the graph on the draw area"""
        if self.thermal_data is None:
            self.init_graph_data()

        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        draw_graph_background_and_border(width, height, cr)
        legend_x = draw_graph_legend(
            THERMAL_GRAPH_COLORS_RGBF,
            width,
            cr,
            220,
        )
        draw_graph_data(
            self.thermal_data,
            THERMAL_GRAPH_COLORS_RGBF,
            legend_x,
            height,
            cr,
            y_lim=(0, 70),
        )

    def update_graph(self):
        """Update the graph values for real-time rendering"""
        if self.util_data is None:  # Graph data not initialized
            return True

        self.util_data[CPU_UTIL_KEY] = self.eventHandler.cpu_util_samples.copy()
        self.util_data[GPU_UTIL_KEY] = self.eventHandler.gpu_util_samples.copy()
        self.util_data[MEM_UTIL_KEY] = self.eventHandler.mem_util_samples.copy()
        self.thermal_data[CPU_THERMAL_KEY] = self.eventHandler.cpu_util_samples.copy()
        self.thermal_data[GPU_THERMAL_KEY] = self.eventHandler.gpu_util_samples.copy()
        self.thermal_data[MEM_THERMAL_KEY] = self.eventHandler.mem_util_samples.copy()
        # For each wave, pop the oldest sample and append a new one
        """
        If you want to simulate a wave, modify can use the following code
        elapsed = time.time()
        for i in range(3):
            self.graph_data[i].pop(0)
            # Eachwave has a different phase
            new_value = int(30 * math.sin(elapsed * 2 + self.phases[i]))
            self.graph_data[i].append(new_value)
        """
        # Request a redraw
        self.eventHandler.GraphDrawAreaTop.queue_draw()
        self.eventHandler.GraphDrawAreaBottom.queue_draw()
        return True

    def localApp(self):
        global GladeBuilder

        GladeBuilder.add_from_file(LAYOUT_PATH)
        GladeBuilder.connect_signals(self.eventHandler)

        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        provider.load_from_path(os.path.join(RESOURCE_FOLDER, "app.css"))
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.eventHandler.MainWindow = GladeBuilder.get_object("mainWindow")
        self.eventHandler.MainWindow.connect("destroy", self.eventHandler.exit)
        self.eventHandler.aboutWindow = GladeBuilder.get_object("aboutWindow")
        self.eventHandler.FPSRate0 = GladeBuilder.get_object("FPS_rate_0")
        self.eventHandler.FPSRate1 = GladeBuilder.get_object("FPS_rate_1")
        self.eventHandler.CPU_load = GladeBuilder.get_object("CPU_load")
        self.eventHandler.GPU_load = GladeBuilder.get_object("GPU_load")
        self.eventHandler.MEM_load = GladeBuilder.get_object("MEM_load")
        self.eventHandler.CPU_temp = GladeBuilder.get_object("CPU_temp")
        self.eventHandler.GPU_temp = GladeBuilder.get_object("GPU_temp")
        self.eventHandler.MEM_temp = GladeBuilder.get_object("MEM_temp")
        self.eventHandler.TopBox = GladeBuilder.get_object("TopBox")
        self.eventHandler.DataGrid = GladeBuilder.get_object("DataGrid")
        self.eventHandler.BottomBox = GladeBuilder.get_object("BottomBox")
        self.eventHandler.DrawArea1 = GladeBuilder.get_object("DrawArea1")
        self.eventHandler.DrawArea2 = GladeBuilder.get_object("DrawArea2")
        self.eventHandler.GraphDrawAreaTop = GladeBuilder.get_object("GraphDrawAreaTop")
        self.eventHandler.GraphDrawAreaBottom = GladeBuilder.get_object(
            "GraphDrawAreaBottom"
        )
        # TODO: Dynamic sizing, positioning
        self.eventHandler.GraphDrawAreaTop.connect("draw", self.on_util_graph_draw)
        self.eventHandler.GraphDrawAreaBottom.connect(
            "draw", self.on_thermal_graph_draw
        )
        # Maybe keep canned generation for situations that perf depends arent available?
        self.util_data = None
        self.thermal_data = None
        self.phases = [0, math.pi / 3, 2 * math.pi / 3]
        GLib.timeout_add(GRAPH_DRAW_PERIOD_ms, self.update_graph)

        self.eventHandler.QProf = QProfProcess()

        # TODO: Can just put these in CSS
        self.eventHandler.MainWindow.override_background_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(23 / 255, 23 / 255, 23 / 255, 0)
        )
        self.eventHandler.TopBox.override_background_color(
            Gtk.StateType.NORMAL, Gdk.RGBA(23 / 255, 23 / 255, 23 / 255, 0.5)
        )

        self.eventHandler.BottomBox.override_background_color(
            Gtk.StateType.NORMAL, Gdk.RGBA(23 / 255, 23 / 255, 23 / 255, 0.5)
        )

        self.eventHandler.MainWindow.set_decorated(False)
        self.eventHandler.MainWindow.set_keep_below(True)
        self.eventHandler.MainWindow.maximize()
        self.eventHandler.MainWindow.show_all()

        self.eventHandler.QProf.start()

        Gtk.main()


if __name__ == "__main__":
    print(TRIA)
    print(f"\nLaunching {APP_HEADER}")
    # Create the video object
    # Add port= if is necessary to use a different one
    video = VaiDemoManager()
