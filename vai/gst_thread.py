import threading
import time

import gi
import subprocess

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst

GST_WATCHDOG_TIMER_MAX_s = 1.5
GST_WATCHDOG_CHECK_PERIOD_ms = 250


class GstPipeline(threading.Thread):

    def __init__(self, gst_command, myName):
        threading.Thread.__init__(self)
        self.gst_command = gst_command
        self.myName= myName

    def camPreview(self, gst_command):
        self.enabled = True
        gst_command = 'exec -a ' + self.myName +' gst-launch-1.0 '+gst_command.replace('(memory:GBM)', '\(memory:GBM\)')+' &'
        subprocess.run(gst_command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                        )

    def close(self):
        subprocess.run(['pkill', '-f', self.myName])  # Send SIGTERM to the process group
        self.enabled = False

    def run(self):
        self.camPreview(self.gst_command)
