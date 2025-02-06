import threading
from time import time

import gi

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst


class camThread(threading.Thread):
    def __init__(self, camID):
        threading.Thread.__init__(self)
        self.camID = camID
        self.cam = None
        self.Frame = None
        self.FrameOk = False
        self.displayTime = 2
        self.frameCounter = 0
        # TODO: Pull fps, leave in FPSDisplaySink
        self.FPS = 0
        self.FPStime = 0
        self.FPSAve = 0.0

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
        elif message.type == Gst.MessageType.ELEMENT:
            struct = message.get_structure()
            if struct.has_name("GstStreamStats"):
                fps = struct.get_double("framerate")
                print("FPS:", fps)

    def camPreview(self, camID):
        self.enabled = True
        # self.cam = cv2.VideoCapture(camID, cv2.CAP_GSTREAMER)
        # if self.cam.isOpened():  # try to get the first frame
        #    self.FrameOk, self.Frame = self.cam.read()
        # else:
        #    self.FrameOk = False

        self.pipeline = Gst.parse_launch(camID)
        self.bus = self.pipeline.get_bus()
        # self.pipeline.set_state(Gst.State.PLAYING)

        self.bus.connect("message", self.on_message, self.loop)
        self.pipeline.set_state(Gst.State.PLAYING)

        while self.enabled:
            msg = self.bus.timed_pop_filtered(1000000000, Gst.MessageType.ANY)
            if msg:
                if msg.type == Gst.MessageType.ELEMENT:
                    struct = msg.get_structure()
                    if struct.has_name("fps-measurements"):
                        fps = struct.get_value("fps")
                        print("FPS:", fps)
            # self.FrameOk, self.Frame = self.cam.read()

            try:
                if self.FrameOk:

                    self.frameCounter += 1
                    TIME = time() - self.FPStime

                    if (TIME) >= self.displayTime:
                        self.FPS = self.frameCounter / (TIME)
                        self.frameCounter = 0
                        self.FPStime = time()

                    self.FPSAve = (self.FPSAve + self.FPS) / 2
            except:
                self.FPS = 0
                pass

    def close(self):
        if self.cam is not None:
            self.cam.release()
        if self.pipeline is not None:
            self.pipeline.set_state(Gst.State.NULL)
        self.enabled = False
        self.Frame = None

    def FPSAvarage(self):
        return round(self.FPSAve)

    def frame(self):
        return self.Frame

    def frame_available(self):
        return type(self.Frame) != type(None)

    def run(self):
        self.camPreview(self.camID)
