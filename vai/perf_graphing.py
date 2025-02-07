import math
import time

import cairo
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk


class RealTimeGraph(Gtk.Window):
    def __init__(self):
        super().__init__(title="Real-Time Transparent Graph")
        self.set_default_size(1920, 80)
        self.set_app_paintable(True)  # Allow transparent painting

        # Remove window border
        self.set_decorated(False)

        # Set overall window transparency
        self.set_opacity(0.5)

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(1920, 80)
        self.drawing_area.connect("draw", self.on_draw)

        self.add(self.drawing_area)

        # Data for sine wave
        self.x_data = list(range(1920))
        self.y_data = [0] * 1920
        self.start_time = time.time()

        # Refresh at 60 FPS
        GLib.timeout_add(16, self.update_graph)

    def update_graph(self):
        """Update the y-values for the sine wave"""

        elapsed = time.time() - self.start_time
        self.y_data = [
            int(80 // 2 * math.sin((x / 50.0) + elapsed)) for x in self.x_data
        ]

        # Request a redraw
        self.drawing_area.queue_draw()
        return True  # Continue updating

    def on_draw(self, _widget, cr):
        """Render the graph using Cairo with true transparency"""

        # Overlay
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source_rgba(0, 0, 0, 0.3)  # Black with 30% transparency
        cr.paint()

        cr.set_source_rgb(0.996, 0.0, 0.635)  # TRIA pink
        cr.set_line_width(2)

        # Draw sine wave
        cr.move_to(0, 80 // 2 + self.y_data[0])
        for x in range(1, 1920):
            cr.line_to(x, 80 // 2 + self.y_data[x])

        cr.stroke()  # Render the line
