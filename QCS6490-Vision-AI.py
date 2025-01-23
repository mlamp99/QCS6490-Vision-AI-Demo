#!/usr/bin/env python3

import os
import re
import signal
import subprocess
import sys
import threading
from time import sleep, time

import cairo
import cv2
import gi
import psutil

#os.environ["XDG_RUNTIME_DIR"] = "/dev/socket/weston"
#os.environ["WAYLAND_DISPLAY"] = "wayland-1"
#os.environ["GDK_BACKEND"] = "wayland"
#os.environ["LC_ALL"] = "en.utf-8"

#os.environ["QMONITOR_BACKEND_LIB_PATH"] = "/var/QualcommProfiler/libs/backends/"
#os.environ["LD_LIBRARY_PATH"] = "$LD_LIBRARY_PATH:/var/QualcommProfiler/libs/"
#os.environ["PATH"] = "$PATH:/data/shared/QualcommProfiler/bins"


# Locks app version, prevents warnings
gi.require_version('Gdk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, GLib, Gst, Gtk


def app_version():
    """Get the latest tag or commit hash if possible, unknown otherwise"""

    try:
        version = subprocess.check_output(
            ["git", "describe", "--tags", "--always"], text=True
        ).strip()

        return version
    except subprocess.CalledProcessError:
        # Handle errors, such as not being in a Git repository
        return "unknown"


APP_NAME = f"QCS6490 Vision AI"
APP_HEADER = f"{APP_NAME} v({app_version()})"

TRIA = r"""
████████╗██████╗ ██╗ █████╗ 
╚══██╔══╝██╔══██╗██║██╔══██╗
   ██║   ██████╔╝██║███████║
   ██║   ██╔══██╗██║██╔══██║
   ██║   ██║  ██║██║██║  ██║
   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝
"""

GladeBuilder = Gtk.Builder()
APP_FOLDER = os.path.dirname(__file__)
RESOURCE_FOLDER = os.path.join(APP_FOLDER, "resources")
LAYOUT_PATH = os.path.join(RESOURCE_FOLDER, "GSTLauncher.glade")

#camera = "gst-launch-1.0 qtiqmmfsrc name=camsrc  ! video/x-raw,format=NV12 ! videoconvert ! video/x-raw,format=BGRA ,width=640,height=480,framerate=30/1 ! appsink drop=1"
camera = "gst-launch-1.0 camera=x ! videoconvert ! videoscale ! video/x-raw, width=640, height=480, framerate=30/1 ! appsink drop=1"

#pose_detection = "gst-launch-1.0 \
#camera=x ! video/x-raw\(memory:GBM\),format=NV12,width=640,height=480,framerate=30/1,compression=ubwc ! queue ! tee name=split \
#split. ! queue ! qtivcomposer name=mixer ! videoconvert ! video/x-raw,format=BGRA ! appsink drop=1 \
#split. ! queue ! qtimlvconverter ! queue ! qtimltflite delegate=external external-delegate-path=libQnnTFLiteDelegate.so external-delegate-options=QNNExternalDelegate,backend_type=htp; \
#model=/opt/posenet_mobilenet_v1.tflite ! queue ! qtimlvpose threshold=51.0 results=2 module=posenet labels=/opt/posenet_mobilenet_v1.labels \
#constants=Posenet,q-offsets=<128.0,128.0,117.0>,q-scales=<0.0784313753247261,0.0784313753247261,1.3875764608383179>; ! video/x-raw,format=BGRA,width=640,height=360 ! queue ! mixer."


pose_detection = "gst-launch-1.0 \
camera=x ! qtivtransform ! video/x-raw\(memory:GBM\),format=NV12,width=640,height=480,framerate=30/1,compression=ubwc ! \
tee name=split \
split. ! queue ! qtivcomposer name=mixer ! videoconvert ! video/x-raw,format=BGRA ! appsink drop=1 \
split. ! queue ! qtimlvconverter ! qtimltflite delegate=external external-delegate-path=libQnnTFLiteDelegate.so external-delegate-options=QNNExternalDelegate,backend_type=htp; \
model=/opt/posenet_mobilenet_v1.tflite ! qtimlvpose threshold=51.0 results=2 module=posenet labels=/opt/posenet_mobilenet_v1.labels \
constants=Posenet,q-offsets=<128.0,128.0,117.0>,q-scales=<0.0784313753247261,0.0784313753247261,1.3875764608383179>; ! video/x-raw,format=BGRA,width=640,height=360 ! queue ! mixer."

segmentation = "gst-launch-1.0 \
camera=x ! video/x-raw\(memory:GBM\),format=NV12,width=640,height=480,framerate=30/1,compression=ubwc ! queue ! tee name=split \
split. ! queue ! qtivcomposer name=mixer sink_1::alpha=0.5 ! queue ! videoconvert ! video/x-raw,format=BGRA ! appsink drop=1 \
split. ! queue ! qtimlvconverter ! queue ! qtimltflite delegate=external external-delegate-path=libQnnTFLiteDelegate.so external-delegate-options=QNNExternalDelegate,backend_type=htp; \
model=/opt/deeplabv3_resnet50.tflite ! queue ! qtimlvsegmentation module=deeplab-argmax labels=/opt/deeplabv3_resnet50.labels ! video/x-raw,width=256,height=144 ! queue ! mixer."

classification1 = "gst-launch-1.0 \
camera=x ! video/x-raw\(memory:GBM\),format=NV12,width=640,height=480,framerate=30/1,compression=ubwc !queue ! tee name=split \
split. ! queue ! qtivcomposer name=mixer1 ! queue ! videoconvert ! video/x-raw,format=BGRA ! appsink drop=1 \
split. ! queue ! qtimlvconverter ! queue ! qtimlsnpe delegate=dsp model=/opt/inceptionv3.dlc ! queue ! qtimlvclassification threshold=40.0 results=2 module=mobilenet labels=/opt/classification.labels \
! video/x-raw,format=BGRA,width=640,height=480 ! queue ! mixer1."

classification = "gst-launch-1.0 \
camera=x ! video/x-raw\(memory:GBM\),format=NV12,width=640,height=480,framerate=30/1,compression=ubwc !queue ! tee name=split \
split. ! queue ! qtivcomposer name=mixer sink_1::position=\"<30,30>\" sink_1::dimensions=\"<320, 180>\" ! queue ! videoconvert ! video/x-raw,format=BGRA ! appsink drop=1 \
split. ! queue ! qtimlvconverter ! queue ! qtimlsnpe delegate=dsp model=/opt/inceptionv3.dlc ! queue ! qtimlvclassification threshold=40.0 results=2 \
module=mobilenet labels=/opt/classification.labels ! video/x-raw,format=BGRA,width=640,height=360 ! queue ! mixer."

object_detection = "gst-launch-1.0 \
camera=x ! video/x-raw\(memory:GBM\),format=NV12,width=640,height=480,framerate=30/1,compression=ubwc !queue ! tee name=split \
split. ! queue ! qtivcomposer name=mixer1 ! queue ! videoconvert ! video/x-raw,format=BGRA ! appsink drop=1 \
split. ! queue ! qtimlvconverter ! queue ! qtimlsnpe delegate=dsp model=/opt/yolonas.dlc layers=\"</heads/Mul, /heads/Sigmoid>\" ! queue ! qtimlvdetection threshold=51.0 results=10 module=yolo-nas labels=/opt/yolonas.labels \
! video/x-raw,format=BGRA,width=640,height=360 ! queue ! mixer1."



#gst-launch-1.0 qtiqmmfsrc name=camsrc ! "video/x-raw, width=640, height=480, framerate=(fraction)30/1" ! fpsdisplaysink sync=false video-sink="autovideosink" -v

def index_containing_substring(the_list, substring):
    for i, s in enumerate(the_list):
        if substring in s:
              return i
    return -1

class QProfProcess(threading.Thread):
    def __init__(self):
        self.enabled = True
        self.CPU = 0
        self.GPU = 0
        self.MEM = 0
        threading.Thread.__init__(self)

    def run(self):
        ansi_escape_8bit = re.compile(br'(?:\x1B[@-Z\\-_]|[\x80-\x9A\x9C-\x9F]|(?:\x1B\[|\x9B)[0-?]*[ -/]*[@-~])')
        while self.enabled:
            p = subprocess.Popen('qprof \
                                    --profile \
                                    --profile-type async \
                                    --result-format CSV \
                                    --capabilities-list profiler:apps-proc-cpu-metrics profiler:proc-gpu-specific-metrics profiler:apps-proc-mem-metrics \
                                    --profile-time 10 \
                                    --sampling-rate 50 \
                                    --streaming-rate 500 \
                                    --live \
                                    --metric-id-list 4648 4616 4865'.split(),
                                shell=False,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
            while self.enabled:
                #line = p.stdout.readline().decode('utf-8').encode("ascii","ignore")
                line = p.stdout.readline().decode('utf-8').encode("ascii","ignore")
                
                line = ansi_escape_8bit.sub(b'', line)
                if not line:
                    break
                #the real code does filtering here

                if line.find(b'CPU Total Load:') > -1:
                    result = re.search(b'CPU Total Load:(.*)%', line)
                    self.CPU = float(result.group(1))
                    #print ('CPU Usage', self.CPU, '%')
                elif line.find(b'GPU Utilization:') > -1:
                    result = re.search(b'GPU Utilization:(.*)%', line)
                    self.GPU = float(result.group(1))
                    #print ('GPU Usage', self.GPU, '%')
                elif line.find(b'Memory Usage %:') > -1:
                    result = re.search(b'Memory Usage %:(.*)%', line)
                    self.MEM = float(result.group(1))
                    #print ('MEM Usage', self.MEM, '%')
            
            #cleanup output files
            subprocess.call('/bin/rm -rf /data/shared/QualcommProfiler/profilingresults/*', shell=True)

    def Close(self):
        self.enabled = False

    def GetCPU(self):
        return round(self.CPU, 2)
    
    def GetGPU(self):
        return round(self.GPU, 2)

    def GetMEM(self):
        return round(self.MEM, 2)

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

    def camPreview(self,camID):
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

                    self.frameCounter+=1
                    TIME = time() - self.FPStime

                    if (TIME) >= self.displayTime :
                        self.FPS = self.frameCounter / (TIME)
                        self.frameCounter = 0
                        self.FPStime = time()

                    self.FPSAve = (self.FPSAve + self.FPS) / 2
            except: 
                self.FPS = 0
                pass


    def close(self):
        if self.cam != None:
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

class Handler:
    def __init__(self):
        self.demoList = [None, camera, pose_detection, segmentation, classification, object_detection]
        self.demoProcess0 = None
        self.demoProcess1 = None
        self.QProf = None
        self.frame0 = None
        self.frame1 = None

        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, self.exit, "SIGINT")
        #GObject.timeout_add(100,  self.UpdateLoads)
        #GObject.timeout_add(2000, self.UpdateTemp)

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
        GLib.idle_add(self.IdleUpdateLabels, self.CPU_load, '{:.2f}'.format(self.QProf.GetCPU(), 2))
        GLib.idle_add(self.IdleUpdateLabels, self.GPU_load, '{:.2f}'.format(self.QProf.GetGPU(), 2))
        GLib.idle_add(self.IdleUpdateLabels, self.MEM_load, '{:.2f}'.format(self.QProf.GetMEM(), 2))
        return True

    def UpdateTemp(self):
        temps = psutil.sensors_temperatures()
        if temps:
            cpuTemp = 0
            gpuTemp = 0
            memTemp = 0
            for name, entries in temps.items():
                for entry in entries:
                    if name == 'cpu0_thermal':
                        cpuTemp = cpuTemp + entry.current
                    elif name == 'cpu1_thermal':
                        cpuTemp = cpuTemp + entry.current
                    elif name == 'cpu2_thermal':
                        cpuTemp = cpuTemp + entry.current
                    elif name == 'cpu3_thermal':
                        cpuTemp = cpuTemp + entry.current
                    elif name == 'cpu4_thermal':
                        cpuTemp = cpuTemp + entry.current
                    elif name == 'cpu5_thermal':
                        cpuTemp = cpuTemp + entry.current
                    elif name == 'cpu6_thermal':
                        cpuTemp = cpuTemp + entry.current
                    elif name == 'cpu7_thermal':
                        cpuTemp = cpuTemp + entry.current
                    elif name == 'cpu8_thermal':
                        cpuTemp = cpuTemp + entry.current
                    elif name == 'cpu9_thermal':
                        cpuTemp = cpuTemp + entry.current
                    elif name == 'cpu10_thermal':
                        cpuTemp = cpuTemp + entry.current
                    elif name == 'cpu11_thermal':
                        cpuTemp = cpuTemp + entry.current
                    elif name == 'ddr_thermal':
                        memTemp = entry.current
                    elif name == 'video_thermal':
                        gpuTemp = entry.current

            GLib.idle_add(self.IdleUpdateLabels, self.CPU_temp, '{:.2f}'.format(cpuTemp/12, 2))
            GLib.idle_add(self.IdleUpdateLabels, self.GPU_temp, '{:.2f}'.format(gpuTemp, 2))
            GLib.idle_add(self.IdleUpdateLabels, self.MEM_temp, '{:.2f}'.format(memTemp, 2))
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

    def getCommand(self, demoIndex, streamIndex):
        command = self.demoList[demoIndex][:]
        if(streamIndex == 0):
            #command = command.replace('camera=x', 'camera=0')
            command = command.replace('camera=x', 'v4l2src device=/dev/video17')
        else:
            command = command.replace('camera=x', 'camera=1')

        return command

    def demo0_selection_changed_cb(self, combo):
        if self.demoProcess0 is not None:
            #end previous process
            self.demoProcess0.close()
            sleep(1)

        index = combo.get_active()
        if index == 0:
            self.demoProcess0 = None
        else:
            self.demoProcess0 = camThread(self.getCommand(index,0))
            self.demoProcess0.start()

    def demo1_selection_changed_cb(self, combo):
        if self.demoProcess1 is not None:
            #end previous process
            self.demoProcess1.close()
            sleep(1)

        index = combo.get_active()
        if index == 0:
            self.demoProcess1 = None
        else:
            self.demoProcess1 = camThread(self.getCommand(index,1))
            self.demoProcess1.start()

    def IdleUpdateLabels(self, label, text):
        label.set_text(text)

    def CapImage_event1(self, widget, context):
        try:
            if self.demoProcess0.frame_available():
                self.frame0 = self.demoProcess0.frame()
                
                self.frame0 = cv2.cvtColor(self.frame0[:,:,::-1], cv2.COLOR_BGR2RGBA)
                H, W, C = self.frame0.shape

                # {.. insert code to modify alpha channel here..}
                surface = cairo.ImageSurface.create_for_data(self.frame0, cairo.FORMAT_ARGB32, W, H)                
                
                #surface = cairo.ImageSurface.create_for_data(self.frame0, cairo.FORMAT_ARGB32, W, H)
                CWidth = widget.get_allocation().width
                CHeight = widget.get_allocation().height

                if CHeight/H < CWidth/W:
                    frameScale = CHeight/H
                else:
                    frameScale = CWidth/W
                
                context.scale(frameScale, frameScale)
                context.set_source_surface(surface, ((CWidth/frameScale) - W)/2,  ((CHeight/frameScale) - H)/2)
                context.paint()
            GLib.idle_add(self.IdleUpdateLabels, self.FPSRate0, str(self.demoProcess0.FPSAvarage()))
        except: 
            GLib.idle_add(self.IdleUpdateLabels, self.FPSRate0, "0")
            pass
        widget.queue_draw()

    def CapImage_event2(self, widget, context):
        try:
            if self.demoProcess1.frame_available():
                self.frame1 = self.demoProcess1.frame()
                H, W, C = self.frame1.shape
                surface = cairo.ImageSurface.create_for_data(self.frame1, cairo.FORMAT_ARGB32, W, H)
                CWidth = widget.get_allocation().width
                CHeight = widget.get_allocation().height

                if CHeight/H < CWidth/W:
                    frameScale = CHeight/H
                else:
                    frameScale = CWidth/W
                
                context.scale(frameScale, frameScale)
                context.set_source_surface(surface, ((CWidth/frameScale) - W)/2,  ((CHeight/frameScale) - H)/2)
                context.paint()
            GLib.idle_add(self.IdleUpdateLabels, self.FPSRate1, str(self.demoProcess1.FPSAvarage()))
        except: 
            GLib.idle_add(self.IdleUpdateLabels, self.FPSRate1, "0")
            pass
        widget.queue_draw()
        
class Video():
    def __init__(self, port=7001):
        Gst.init(None)

        self.eventHandler = Handler()
        self.running = True

        self.localAppThread = threading.Thread(target=self.localApp)
        self.localAppThread.start()

    def localApp(self):
        global GladeBuilder

        GladeBuilder.add_from_file(LAYOUT_PATH)
        GladeBuilder.connect_signals(self.eventHandler)

        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        provider.load_from_path(os.path.join(RESOURCE_FOLDER, "app.css"))
        Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

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

        self.eventHandler.demoProcess0 = camThread(self.eventHandler.getCommand(1,0))
        self.eventHandler.demoProcess1 = camThread(self.eventHandler.getCommand(1,1))
        self.eventHandler.QProf = QProfProcess()


        self.eventHandler.MainWindow.fullscreen()
        self.eventHandler.MainWindow.show_all()

        #self.eventHandler.demoProcess0.start()
        #while self.eventHandler.demoProcess0.FrameOk == False:
        #    sleep(0.1)

        #self.eventHandler.demoProcess1.start()
        #while self.eventHandler.demoProcess1.FrameOk == False:
        #    sleep(0.1)

        #self.eventHandler.QProf.start()

        Gtk.main()
                          
if __name__ == '__main__':
    print(TRIA)
    print(f"\nLaunching {APP_HEADER}")
    # Create the video object
    # Add port= if is necessary to use a different one
    video = Video()
