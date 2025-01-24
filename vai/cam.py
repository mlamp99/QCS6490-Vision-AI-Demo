import threading
from time import time

import cv2


class camThread(threading.Thread):
    def __init__(self, camID):
        threading.Thread.__init__(self)
        self.camID = camID
        self.cam = None
        self.Frame = None
        self.FrameOk = False
        self.displayTime = 2
        self.frameCounter = 0
        self.FPS = 0
        self.FPStime = 0
        self.FPSAve = 0.0

    def camPreview(self, camID):
        self.enabled = True
        self.cam = cv2.VideoCapture(camID, cv2.CAP_GSTREAMER)
        if self.cam.isOpened():  # try to get the first frame
            self.FrameOk, self.Frame = self.cam.read()
        else:
            self.FrameOk = False

        while self.enabled:
            self.FrameOk, self.Frame = self.cam.read()

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
