import subprocess

DEFAULT_DISPLAY = "waylandsink x=10 y=50 width=640 height=480 async=true sync=false"

# NOTE: These commands may be processed by application
# TODO: add FPS support for camera
CAMERA = f"<DATA_SRC> ! qtivtransform ! video/x-raw(memory:GBM),format=NV12,width=640,height=480,framerate=30/1,compression=ubwc ! {DEFAULT_DISPLAY}"

POSE_DETECTION = "<DATA_SRC> ! qtivtransform ! video/x-raw(memory:GBM),format=NV12,width=640,height=480,framerate=30/1,compression=ubwc ! tee name=split \
split. ! queue ! qtivcomposer name=mixer ! <DISPLAY> \
split. ! queue ! qtimlvconverter ! qtimltflite delegate=external external-delegate-path=libQnnTFLiteDelegate.so external-delegate-options=QNNExternalDelegate,backend_type=htp; \
model=/opt/posenet_mobilenet_v1.tflite ! qtimlvpose threshold=51.0 results=2 module=posenet labels=/opt/posenet_mobilenet_v1.labels \
constants=Posenet,q-offsets=<128.0,128.0,117.0>,q-scales=<0.0784313753247261,0.0784313753247261,1.3875764608383179>; ! video/x-raw,format=BGRA,width=640,height=480 ! mixer."

SEGMENTATION = "<DATA_SRC> ! qtivtransform ! video/x-raw(memory:GBM),format=NV12,width=640,height=360,framerate=30/1,compression=ubwc ! tee name=split \
split. ! queue ! qtivcomposer name=mixer sink_1::alpha=0.5 ! queue ! <DISPLAY> \
split. ! queue ! qtimlvconverter ! queue ! qtimltflite delegate=external external-delegate-path=libQnnTFLiteDelegate.so external-delegate-options=QNNExternalDelegate,backend_type=htp; \
model=/opt/deeplabv3_resnet50.tflite ! queue ! qtimlvsegmentation module=deeplab-argmax labels=/opt/deeplabv3_resnet50.labels ! video/x-raw,width=256,height=144 ! queue ! mixer."

CLASSIFICATION = '<DATA_SRC> ! qtivtransform ! video/x-raw(memory:GBM),format=NV12,width=640,height=480,framerate=30/1,compression=ubwc !queue ! tee name=split \
split. ! queue ! qtivcomposer name=mixer sink_1::position="<30,30>" sink_1::dimensions="<320, 180>" ! queue ! <DISPLAY> \
split. ! queue ! qtimlvconverter ! queue ! qtimlsnpe delegate=dsp model=/opt/inceptionv3.dlc ! queue ! qtimlvclassification threshold=40.0 results=2 \
module=mobilenet labels=/opt/classification.labels ! video/x-raw,format=BGRA,width=640,height=360 ! queue ! mixer.'

OBJECT_DETECTION = '<DATA_SRC> ! qtivtransform ! video/x-raw(memory:GBM),format=NV12,width=640,height=480,framerate=30/1,compression=ubwc !queue ! tee name=split \
split. ! queue ! qtivcomposer name=mixer1 ! queue ! <DISPLAY> \
split. ! queue ! qtimlvconverter ! queue ! qtimlsnpe delegate=dsp model=/opt/yolonas.dlc layers="</heads/Mul, /heads/Sigmoid>" ! queue ! qtimlvdetection threshold=51.0 results=10 module=yolo-nas labels=/opt/yolonas.labels \
! video/x-raw,format=BGRA,width=640,height=480 ! queue ! mixer1.'


APP_NAME = f"QCS6490 Vision AI"

TRIA = r"""
████████╗██████╗ ██╗ █████╗ 
╚══██╔══╝██╔══██╗██║██╔══██╗
   ██║   ██████╔╝██║███████║
   ██║   ██╔══██╗██║██╔══██║
   ██║   ██║  ██║██║██║  ██║
   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝
"""


def app_version():
    """Get the latest tag or commit hash if possible, unknown otherwise"""

    try:
        version = subprocess.check_output(
            ["git", "describe", "--tags", "--always"], text=True
        ).strip()
        date = subprocess.check_output(
            ["git", "log", "-1", "--format=%cd", "--date=short"], text=True
        ).strip()

        return f"{version} {date}"
    except subprocess.CalledProcessError:
        # Handle errors, such as not being in a Git repository
        return "unknown"


APP_HEADER = f"{APP_NAME} v({app_version()})"
