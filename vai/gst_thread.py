import threading
import time

import gi

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst

GST_WATCHDOG_TIMER_MAX_s = 1.5
GST_WATCHDOG_CHECK_PERIOD_ms = 250


class GstPipeline(threading.Thread):

    def __init__(self, gst_command):
        threading.Thread.__init__(self)
        self.gst_command = gst_command

        # Depending upon where you place the handoff signal, you may need to adjust this logic
        # If you have the handoff signal directly after the camera source, you need to consider starting
        # the timer after the first handoff signal, otherwise you may trigger the watchdog immediately while
        # the pipeline is still starting up (camera is initializing).
        # Thus, the first buffer time is set to None and the timer is not started until the first handoff signal.
        # TODO: I think it looks better when all gstramer pipelines are restarted (at the same time) if a single one fails.
        self.last_buffer_time = None
        self.loop = GLib.MainLoop()
        self.pipeline = None
        self.bus = None

    def on_buffer_handoff(self, _element, _buffer):
        """Run when a buffer is handed off to the next element in the pipeline."""
        self.last_buffer_time = time.monotonic()
        return Gst.FlowReturn.OK

    def watchdog_timer_check(self):
        """Check if the pipeline has stopped producing buffers. If so, restart it."""

        # This model assumes we dont want to start the timer until the first buffer is received (see comment in __init__)
        if self.last_buffer_time is None or not self.enabled:
            return True
        elif time.monotonic() - self.last_buffer_time > GST_WATCHDOG_TIMER_MAX_s:
            print("Watchdog triggered, restarting pipeline")
            self.last_buffer_time = None  # Prevent the watchdog from triggering multiple times in quick succession.
            self.pipeline.set_state(Gst.State.NULL)
            self.camPreview(self.gst_command)

        return True

    def on_message(_bus, message, loop):
        if message.type == Gst.MessageType.EOS:
            loop.quit()
        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print("Error:", err, debug)
            loop.quit()

    def camPreview(self, gst_command):
        self.enabled = True

        self.pipeline = Gst.parse_launch(gst_command)
        identity_element = self.pipeline.get_by_name("id")
        identity_element.connect("handoff", self.on_buffer_handoff)
        self.bus = self.pipeline.get_bus()

        self.bus.connect("message", self.on_message, self.loop)
        self.pipeline.set_state(Gst.State.PLAYING)
        GLib.timeout_add(GST_WATCHDOG_CHECK_PERIOD_ms, self.watchdog_timer_check)

    def close(self):
        if self.pipeline is not None:
            self.pipeline.set_state(Gst.State.NULL)
        self.enabled = False
        self.last_buffer_time = None

    def run(self):
        self.camPreview(self.gst_command)
