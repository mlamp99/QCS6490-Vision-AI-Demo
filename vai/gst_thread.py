import threading

import gi

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst


class GstPipeline(threading.Thread):
    def __init__(self, camID):
        threading.Thread.__init__(self)
        self.camID = camID
        self.cam = None

        self.loop = GLib.MainLoop()
        self.pipeline = None
        self.bus = None

    def on_message(bus, message, loop):
        if message.type == Gst.MessageType.EOS:
            loop.quit()
        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print("Error:", err, debug)
            loop.quit()

    def camPreview(self, camID):
        self.enabled = True

        self.pipeline = Gst.parse_launch(camID)
        self.bus = self.pipeline.get_bus()

        self.bus.connect("message", self.on_message, self.loop)
        self.pipeline.set_state(Gst.State.PLAYING)

    def close(self):
        if self.cam is not None:
            self.cam.release()
        if self.pipeline is not None:
            self.pipeline.set_state(Gst.State.NULL)
        self.enabled = False

    def run(self):
        self.camPreview(self.camID)
