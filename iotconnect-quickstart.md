# QCS6490 Vision AI Demo: IoTConnect Quickstart

## Table of Contents
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Cloud Account & Device Template Setup](#cloud-account--device-template-setup)
- [Project Layout](#project-layout)
- [Device Setup](#device-setup)
- [Launch the IoTConnect-enabled Demo](#launch-the-iotconnect-enabled-demo)
- [Telemetry & Commands](#telemetry--commands)
  - [Telemetry Fields](#telemetry-fields)
  - [Supported Commands](#supported-commands)
    - [start_demo <camera> <pipeline>](#start_demo--camera--pipeline)
    - [stop_demo <camera>](#stop_demo--camera)
  - [How to Use Telemetry & Commands](#how-to-use-telemetry--commands)
- [Summary](#summary)

---

## Introduction

This Quickstart will guide you through installing the Python Lite SDK, generating (or uploading) your device credentials, and validating connectivity. Once completed, the certificates and `iotconnect-config.json` will be placed in `iotc_config/`, which is exactly where your `visionai-iotc.py` expects them.

---

## Prerequisites

- **Bash shell** (Linux on the VisionAI-Kit, or Git Bash on Windows).
- **Python 3** (3.6 or newer) with pip.
- **`openssl`** (CLI).
- **`curl`** or **`wget`** for fetching the Quickstart script.
- A valid IoTConnect subscription (AWS- or Azure-based). If you’ve never signed up, you can get a free trial at:
  - AWS: https://subscription.iotconnect.io/subscribe?cloud=aws
  - Azure: https://subscription.iotconnect.io/subscribe?cloud=azure
- If you’ve previously installed the full [IoTConnect Python SDK](https://github.com/avnet-iotconnect/iotc-python-sdk), install the Lite SDK into a separate virtual environment — the full SDK upgrades `paho-mqtt`, which can break the Lite runtime.

---

## Cloud Account & Device Template Setup

1. **Log in** to your IoTConnect account (AWS or Azure version).
2. Confirm you have at least one **Device Template** that matches the telemetry you’ll send (CPU, GPU, memory, temperatures, etc.).
3. If you don’t already have a matching template, download and import a JSON template from the IoTConnect GitHub (e.g., a generic “plitedemo” template):
   - Right-click to download:
     ```
     https://raw.githubusercontent.com/avnet-iotconnect/avnet-iotc-mtb-xensiv-example/main/files/plitedemo-template.json
     ```
   - In the IoTConnect web portal, navigate to **Device → Templates**, click **Create Template**, then **Import** and select that JSON.

> **Tip:** Watch your SPAM folder for the “temporary password” email if this is a new IoTConnect trial.

---

## Project Layout

```
/var/rootdirs/opt/QCS6490-Vision-AI-Demo
├── visionai.py
├── visionai-iotc.py
├── launch_visionai_with_env.sh
├── iotc_config/
│   ├── (empty initially)
│   └── quickstart.sh
└── README.md
```

Your `visionai-iotc.py` expects:
```python
DeviceConfig.from_iotc_device_config_json_file(
    device_config_json_path="iotc_config/iotconnect-config.json",
    device_cert_path="iotc_config/device-cert.pem",
    device_pkey_path="iotc_config/device-pkey.pem"
)
```
so the Quickstart must generate those three files in `iotc_config/`.

---

## Device Setup

1. **Change into the `iotc_config/` folder**:
   ```bash
   cd /var/rootdirs/opt/QCS6490-Vision-AI-Demo/iotc_config
   ```
2. **Install the Lite SDK** (if not already installed system-wide):
   ```bash
   python3 -m pip install iotconnect-sdk-lite
   ```
3. **Fetch and run the Quickstart script**. Use either **curl** or **wget**:
   ```bash
   # Using curl:
   curl -sOJ 'https://raw.githubusercontent.com/avnet-iotconnect/iotc-python-lite-sdk/refs/heads/main/scripts/quickstart.sh'      && bash ./quickstart.sh
   ```
   ```bash
   # Or using wget:
   wget -qN 'https://raw.githubusercontent.com/avnet-iotconnect/iotc-python-lite-sdk/refs/heads/main/scripts/quickstart.sh'      && bash ./quickstart.sh
   ```
4. **Follow the prompts**. After completion, you’ll see:
   ```
   (re)connecting...
   Awaiting MQTT connection establishment...
   waiting to connect...
   Connected. Reason Code: Success
   MQTT connected
   Connected in 542ms
   > {"d":[{"d":{"sdk_version":"1.0.2","version":"1.0.0","random":29}}]}
   ```
   Then you can try:
   ```
   > send-command set-user-led 50 255 0
   Received command set-user-led ['50','255','0']
   Setting User LED to R:50 G:255 B:0
   ```
5. **Verify output files**. After Quickstart:
   ```
   /var/rootdirs/opt/QCS6490-Vision-AI-Demo/iotc_config/
   ├── device-cert.pem
   ├── device-pkey.pem
   └── iotcDeviceConfig.json
   ```
   These match what `visionai-iotc.py` expects.
6. **Check permissions**. Ensure the device user can read them:
   ```bash
   chmod 644 device-cert.pem device-pkey.pem iotcDeviceConfig.json
   ```

---

## Launch the IoTConnect-enabled Demo

Once Quickstart has created your certificates and JSON, return to the project root and run:

```bash
cd /var/rootdirs/opt/QCS6490-Vision-AI-Demo
sudo bash ./launch_visionai_with_env.sh
```

- Within three seconds, press **“i”** to select the IoTConnect‐enabled demo (`visionai-iotc.py`).
- If you don’t press anything, the standard `visionai.py` will run.

Behind the scenes, `visionai-iotc.py` calls:
```python
DeviceConfig.from_iotc_device_config_json_file(
    device_config_json_path="iotc_config/iotcDeviceConfig.json",
    device_cert_path="iotc_config/device-cert.pem",
    device_pkey_path="iotc_config/device-pkey.pem"
)
self.iotc = Client(config=device_config, callbacks=Callbacks(command_cb=…))
self.iotc.connect()
```
So as long as your certs/JSON are in `iotc_config/`, the SDK will find them.

---

## Telemetry & Commands

Once the device is connected, `visionai-iotc.py` will send telemetry every 5 seconds and listen for two commands. Below is a summary of what the demo sends, what commands it supports, and how to invoke them.

### Telemetry Fields

Every 5 seconds the demo gathers system metrics and publishes this JSON payload (all values are numeric):

- **cpu_usage** – CPU utilization (0 – 100 percent)
- **gpu_usage** – GPU utilization (0 – 100 percent)
- **memory_usage** – RAM utilization (0 – 100 percent)
- **cpu_temp** – CPU temperature (in °C or sensor units)
- **gpu_temp** – GPU temperature (in °C or sensor units)
- **memory_temp** – Memory subsystem temperature (in °C or sensor units)
- **critical** – A fixed “alert” value (set to 85 in code)

<details>
<summary>Example telemetry JSON</summary>

```json
{
  "cpu_usage": 12.3,
  "gpu_usage":  7.8,
  "memory_usage": 45.6,
  "cpu_temp": 55.0,
  "gpu_temp": 50.2,
  "memory_temp": 48.7,
  "critical": 85
}
```
</details>

> Under the hood:
> ```python
> telemetry = {
>   "cpu_usage": sample_data.get(CPU_UTIL_KEY, 0),
>   "gpu_usage": sample_data.get(GPU_UTIL_KEY, 0),
>   "memory_usage": sample_data.get(MEM_UTIL_KEY, 0),
>   "cpu_temp": sample_data.get(CPU_THERMAL_KEY, 0),
>   "gpu_temp": sample_data.get(GPU_THERMAL_KEY, 0),
>   "memory_temp": sample_data.get(MEM_THERMAL_KEY, 0),
>   "critical": 85,
> }
> self.iotc.send_telemetry(telemetry)
> ```

You can confirm these fields arrive under **Device → Telemetry** in the portal once the device is online.

---

### Supported Commands

The demo listens for two device‐to‐cloud commands (C2D) from IoTConnect. In both cases, the device logs:
```
[IOTCONNECT] Command received: <cmd_name>
```
… then performs a GUI update and sends back an acknowledgment.

#### start_demo <camera> <pipeline>

- **Purpose**: Switch the specified camera widget to a new demo pipeline (e.g., classification, detection, etc.).
- **Arguments**:
  - `camera` – Either `cam1` or `cam2` (case-insensitive).
  - `pipeline` – A string `"1"` through `"6"`, mapping to one of six demo modes in the GUI.
- **Behavior**:
  - If `camera` is `cam1`:
    ```python
    GLib.idle_add(self.eventHandler.demo_selection0.set_active, pipeline_index)
    ack_message = f"CAM1 started {pipeline}"
    ack_status = C2dAck.CMD_SUCCESS_WITH_ACK
    ```
  - If `camera` is `cam2`:
    ```python
    GLib.idle_add(self.eventHandler.demo_selection1.set_active, pipeline_index)
    ack_message = f"CAM2 started {pipeline}"
    ack_status = C2dAck.CMD_SUCCESS_WITH_ACK
    ```
  - Otherwise: `ValueError("Invalid camera: …")` and a failure ack.
- **Example**:
  1. In IoTConnect → Device → Commands, send:
     - **Command name**: `start_demo`
     - **Arguments**: `["cam1","2"]`
  2. Device log:
     ```
     [IOTCONNECT] Command received: start_demo
     ```
  3. GUI dropdown for Camera 1 switches to demo #2, and you see:
     ```
     Received command start_demo ['cam1','2']
     CAM1 started 2
     ```
  4. In the portal, Command Ack shows **SUCCESS_WITH_ACK**, message `"CAM1 started 2"`.

#### stop_demo <camera>

- **Purpose**: Stop the demo on the specified camera (i.e., switch back to “off”).
- **Arguments**:
  - `camera` – Either `cam1` or `cam2` (case-insensitive).
- **Behavior**:
  - If `camera` is `cam1`:
    ```python
    GLib.idle_add(self.eventHandler.demo_selection0.set_active, 0)
    ack_message = "CAM1 demo stopped"
    ack_status = C2dAck.CMD_SUCCESS_WITH_ACK
    ```
  - If `camera` is `cam2`:
    ```python
    GLib.idle_add(self.eventHandler.demo_selection1.set_active, 0)
    ack_message = "CAM2 demo stopped"
    ack_status = C2dAck.CMD_SUCCESS_WITH_ACK
    ```
  - Otherwise: `ValueError("Invalid camera: …")` and a failure ack.
- **Example**:
  1. In IoTConnect → Device → Commands, send:
     - **Command name**: `stop_demo`
     - **Arguments**: `["cam2"]`
  2. Device log:
     ```
     [IOTCONNECT] Command received: stop_demo
     ```
  3. GUI dropdown for Camera 2 resets to index 0, and you see:
     ```
     Received command stop_demo ['cam2']
     CAM2 demo stopped
     ```
  4. In the portal, Command Ack shows **SUCCESS_WITH_ACK**, message `"CAM2 demo stopped"`.

> Under the hood (excerpt from `visionai-iotc.py`):
>
> ```python
> def handle_iotconnect_command(self, command):
>     cmd_name = command.command_name
>
>     if cmd_name == 'start_demo':
>         camera = command.command_args[0].lower()
>         pipeline = command.command_args[1].lower()
>         pipeline_mapping = {"1":1, "2":2, "3":3, "4":4, "5":5, "6":6}
>         pipeline_index = pipeline_mapping.get(pipeline)
>         if camera == 'cam1':
>             GLib.idle_add(self.eventHandler.demo_selection0.set_active, pipeline_index)
>             ack_message = f"CAM1 started {pipeline}"
>             ack_status = C2dAck.CMD_SUCCESS_WITH_ACK
>         elif camera == 'cam2':
>             GLib.idle_add(self.eventHandler.demo_selection1.set_active, pipeline_index)
>             ack_message = f"CAM2 started {pipeline}"
>             ack_status = C2dAck.CMD_SUCCESS_WITH_ACK
>         else:
>             raise ValueError(f"Invalid camera: {camera}")
>         self.iotc.send_command_ack(command, ack_status, ack_message)
>
>     elif cmd_name == 'stop_demo':
>         camera = command.command_args[0].lower()
>         if camera == 'cam1':
>             GLib.idle_add(self.eventHandler.demo_selection0.set_active, 0)
>             ack_message = "CAM1 demo stopped"
>             ack_status = C2dAck.CMD_SUCCESS_WITH_ACK
>         elif camera == 'cam2':
>             GLib.idle_add(self.eventHandler.demo_selection1.set_active, 0)
>             ack_message = "CAM2 demo stopped"
>             ack_status = C2dAck.CMD_SUCCESS_WITH_ACK
>         else:
>             raise ValueError(f"Invalid camera: {camera}")
>         self.iotc.send_command_ack(command, ack_status, ack_message)
>
>     else:
>         self.iotc.send_command_ack(command, C2dAck.CMD_FAILED, "Unknown command")
> ```

---

### How to Use Telemetry & Commands

1. **Verify telemetry arrival**
   - In IoTConnect → Device → Telemetry (select your device), you should see a new message every 5 seconds containing the fields above.
   - If telemetry isn’t appearing, confirm:
     - The device is online (Device → Status).
     - `device-cert.pem`, `device-pkey.pem`, and `iotconnect-config.json` are present in `iotc_config/`.
     - No errors appear on the VisionAI-Kit’s console (e.g., certificate or network errors).

2. **Invoke a command**
   - Go to IoTConnect → Device → Commands (your registered device).
   - Click **“Send Command”**. In the dialog:
     1. Set **Command name** to either `start_demo` or `stop_demo`.
     2. Provide the arguments as a JSON array:
        - For `start_demo`, use `["cam1","3"]` (example).
        - For `stop_demo`, use `["cam2"]` (example).
   - Submit it.
   - Watch the **Command Acknowledgments** section: you should see **STATUS: SUCCESS_WITH_ACK** and the message (e.g., `"CAM1 started 3"`).
   - Observe the VisionAI-Kit GUI: camera 1 or 2’s dropdown will switch (for `start_demo`) or revert to 0 (for `stop_demo`).

3. **Map pipelines to demos**
   - Pipelines `1–6` correspond to the six demo modes in the GUI. The dropdown for each camera usually shows:
     ```
     0: Off
     1: AI Classification
     2: AI Object Detection
     3: AI Pose Estimation
     4: AI Semantic Segmentation
     5: GPU Stress Test
     6: Memory Benchmark
     ```
   - To pick a specific demo via command, send the matching index (as a string) in the second argument.

4. **Stopping a running demo**
   - A `stop_demo` command with `["cam1"]` or `["cam2"]` sets the dropdown to index 0 (“Off”), halting any active demo on that camera.

---

## Summary

- Run Quickstart from `…/QCS6490-Vision-AI-Demo/iotc_config/` so that `device-cert.pem`, `device-pkey.pem`, and `iotconnect-config.json` end up exactly where `visionai-iotc.py` expects them.
- Ensure the new files have `644` permissions so `visionai-iotc.py` can read them.
- Use `launch_visionai_with_env.sh` to pick the IoTConnect demo at runtime.
- Once connected, monitor real‐time system metrics in IoTConnect and switch demos on/off by sending `start_demo`/`stop_demo`.

That’s it—once Quickstart succeeds, your VisionAI‐Kit application will begin sending telemetry and handling commands over IoTConnect without any further manual file copying.