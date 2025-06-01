# QCS6490 Vision AI Demo: /IOTCONNECT Quickstart

## Table of Contents
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Cloud Account & Device Template Setup](#cloud-account--device-template-setup)
- [Project Layout](#project-layout)
- [Device Setup & Certificate Download](#device-setup--certificate-download)
- [Launch the /IOTCONNECT‐Enabled Demo](#launch-the-iotconnect‐enabled-demo)
- [Telemetry & Commands](#telemetry--commands)
  - [Telemetry Fields](#telemetry-fields)
  - [Supported Commands](#supported-commands)
    - [start_demo `<camera>` `<pipeline>`](#start_demo-camera-pipeline)
    - [stop_demo `<camera>`](#stop_demo-camera)
  - [How to Use Telemetry & Commands](#how-to-use-telemetry--commands)
- [Summary](#summary)
- [Links & References](#links--references)

---

## Introduction

This Quickstart guide walks you through:

1. Importing the **TRIA Vision AI Kit 6490** Device Template (provided in this repository).
2. Creating a Device in /IOTCONNECT using that template.
3. Downloading the auto‐generated certificates + configuration JSON.
4. Placing those files into `iotc_config/` so that `visionai-iotc.py` can use them.
5. Validating connectivity and running the Vision AI demo, which sends telemetry and accepts commands via /IOTCONNECT.

---

## Prerequisites

- A working **Bash shell** on your VisionAI‐Kit (or Git Bash if on Windows).
- **Python 3** (3.6+) with `pip`.
- **`openssl`** CLI (optional, for inspecting certificates).
- **`curl`** or **`wget`** (for fetching files if needed).
- An active **/IOTCONNECT** subscription (AWS‐ or Azure‐based). If you don’t already have one, sign up for a free trial:
  - AWS:  
    ```
    https://subscription.iotconnect.io/subscribe?cloud=aws
    ```
  - Azure:  
    ```
    https://subscription.iotconnect.io/subscribe?cloud=azure
    ```
- (Optional) If you previously installed the full IoTConnect Python SDK, create a separate virtual environment before installing the Lite SDK. The Lite SDK pins `paho-mqtt` to versions guaranteed to run with `visionai-iotc.py`.

---

## Cloud Account & Device Template Setup

Before creating a Device, you need a Device Template in /IOTCONNECT that matches exactly the telemetry attributes and commands the TRIA Vision AI Kit 6490 demo will send/receive.

### 1. Download (or Clone) the TRIA 6490 Device Template JSON

We’ve already defined a complete template JSON in this repository. It includes:

- **Telemetry attributes**:  
  `cpu_usage`, `gpu_usage`, `memory_usage`, `cpu_temp`, `gpu_temp`, `memory_temp`, `critical`
- **Commands**:  
  `start_demo`, `stop_demo`

Simply use the file that’s already in [`iotconnect/tria_6490_device_template.JSON`](iotconnect/tria_6490_device_template.JSON) of this repo.

> **Important**: Do not modify this file unless you need to add/remove telemetry fields or commands. If you do edit it, re‐import it under a new Template Code.

#### 2. Import the TRIA Template into /IOTCONNECT

1. **Log in** to your /IOTCONNECT portal (AWS or Azure version).

2. In the left navigation menu, click **Devices → Templates**.

   ![Select “Templates”](iotconnect/images/select_template.png)

3. Click **Create Template** (top‐right).

   ![Create Template](iotconnect/images/create_template.png)

4. In the “Create Template” page, click **Import** (top‐right).

   ![Select “Import Template”](iotconnect/images/select_import_template.png)

5. **Upload** `tria_6490_device_template.JSON`   
   - Once uploaded, click **Save**.
   - You should now see a new template named **TRIA Vision AI Kit 6490** (or similar) in your template list, with:
     - **Auth Type**: x509
     - **Message Version**: 2.1
     - **Attributes 7** (for the telemetry fields)
     - **Commands 2** (`start_demo`, `stop_demo`)

> **Tip**: If you ever need to tweak the template (for example, add a new telemetry field), edit `tria_6490_device_template.JSON` in your local folder, then re‐import under a fresh Template Code (e.g. `TRIA Vision AI Kit 6490 v2`). Always note the exact Template Code spelling.

---

## Project Layout

Your local project structure should now look like this (on the VisionAI‐Kit or your dev machine):

```
/var/rootdirs/opt/QCS6490-Vision-AI-Demo
├── visionai.py
├── visionai-iotc.py
├── launch_visionai_with_env.sh
├── iotc_config/              ← (initially empty until you download certs)
│   └── quickstart.sh         ← (only if you opt to auto‐generate via script)
├── iotconnect/
│   ├── images/               ← contains the screenshots referenced below
│   │   ├── select_template.png
│   │   ├── create_template.png
│   │   └── select_import_template.png
│   ├── tria_6490_device_template.JSON
│   └── iotconnect-quickstart.md   ← (this file)
└── README.md
```

**Important**:  
`visionai-iotc.py` looks specifically in `iotc_config/` for these three files:

```python
DeviceConfig.from_iotc_device_config_json_file(
    device_config_json_path="iotc_config/iotcDeviceConfig.json",
    device_cert_path="iotc_config/device-cert.pem",
    device_pkey_path="iotc_config/device-pkey.pem"
)
```

So **before** running the IoTConnect variant of the demo, you must have:

```
iotc_config/device-cert.pem
iotc_config/device-pkey.pem
iotc_config/iotcDeviceConfig.json
```

---

## Device Setup & Certificate Download

You have two options for provisioning your device and retrieving certificates:

- **Option A (Recommended)**: Create a Device in the /IOTCONNECT portal and **Download Device Configuration** (certificate + key + JSON).
- **Option B**: Use the interactive Quickstart script to auto‐generate certificates server‐side and save them locally.

### Option A: Download from /IOTCONNECT Portal

1. In the /IOTCONNECT portal, navigate to **Devices → Devices**.

   You should see a list of existing devices (if any).

2. Click **Create Device** (top‐right).

   ![Select “Create Device”](iotconnect/images/select_template.png)

3. In the **Create Device** form, fill in the fields as follows:
   - **Unique Id**:  
     A short, unique identifier. Example: `QCS6490-01`  
     (This becomes your MQTT clientID.)
   - **Device Name**:  
     A human‐readable name, e.g. `QCS6490-VisionAI-Kit`
   - **Entity**:  
     Select your Entity (company or division). If you only have one, it might be pre‐selected.
   - **Template**:  
     Choose `TRIA Vision AI Kit 6490` (the exact Template Code you just imported).
   - **Device certificate**:  
     Select **Auto-generated (recommended)**.  
     /IOTCONNECT will issue a new x509 cert + private key.
   - **Notes** (optional):  
     e.g. `Vision AI Demo – QCS6490`

   ![Create Device Form](iotconnect/images/create_template.png)

4. Click **Save & View**. You’ll be taken to the Device Info page.

5. On the Device Info page, click the **Download Device Configuration** icon (document + down-arrow).

   ![Download Device Configuration](iotconnect/images/select_import_template.png)

   - A ZIP file named something like `QCS6490-01_iotc_config.zip` will download.
   - Inside that ZIP are exactly:
     ```
     device-cert.pem
     device-pkey.pem
     iotcDeviceConfig.json
     ```

6. **Copy & unzip** these three files into your local `iotc_config/` folder:

   ```bash
   cd /var/rootdirs/opt/QCS6490-Vision-AI-Demo/iotc_config
   unzip ~/Downloads/QCS6490-01_iotc_config.zip
   ```

7. **Verify and fix permissions** so the demo can read them:

   ```bash
   ls -l device-cert.pem device-pkey.pem iotcDeviceConfig.json
   chmod 644 device-cert.pem device-pkey.pem iotcDeviceConfig.json
   ```

   Now, your `iotc_config/` directory should contain:
   ```
   /var/rootdirs/opt/QCS6490-Vision-AI-Demo/iotc_config/
   ├── device-cert.pem
   ├── device-pkey.pem
   └── iotcDeviceConfig.json
   ```

   **Skip to [Launch the /IOTCONNECT‐Enabled Demo](#launch-the-iotconnect‐enabled-demo) below.**

---

### Option B: Auto‐Generate via Quickstart Script (Alternative)

> **Use this only** if you prefer the script‐driven provisioning flow. The result is the same three files in `iotc_config/`.

1. SSH into your VisionAI‐Kit (or open a terminal) and change into `iotc_config/`:

   ```bash
   cd /var/rootdirs/opt/QCS6490-Vision-AI-Demo/iotc_config
   ```

2. **Install the Lite SDK** (unless you already installed it in a venv):

   ```bash
   python3 -m pip install iotconnect-sdk-lite
   ```

3. **Download and run** the Quickstart script:

   ```bash
   wget -qN 'https://raw.githubusercontent.com/avnet-iotconnect/iotc-python-lite-sdk/refs/heads/main/scripts/quickstart.sh'
   chmod +x quickstart.sh
   bash ./quickstart.sh
   ```

4. **Follow the interactive prompts** exactly. You will be asked for:
   - **Cloud** (AWS or Azure)
   - **Subscription ID** (from /IOTCONNECT → Settings)
   - **Entity ID** (numeric, from your portal)
   - **Template Code** (type exactly: `TRIA Vision AI Kit 6490`)
   - **Unique ID** (e.g. `QCS6490-01`) & **Device Name** (e.g. `QCS6490-VisionAI-Kit`)
   - (Optional) **Notes**.

5. After the script completes, you will see something like:

   ```
   Connected. Reason Code: Success
   MQTT connected (ClientID: QCS6490-01)
   > {"d":[{"d":{"sdk_version":"1.0.2","version":"1.0.0","random":29}}]}
   ```

   And in your current directory (`iotc_config/`) you now have:
   ```
   device-cert.pem
   device-pkey.pem
   iotcDeviceConfig.json
   ```

6. **Verify** and set permissions:

   ```bash
   ls -l device-cert.pem device-pkey.pem iotcDeviceConfig.json
   chmod 644 device-cert.pem device-pkey.pem iotcDeviceConfig.json
   ```

> **Note**: If you check the /IOTCONNECT portal under **Devices → Devices**, you’ll see that the Quickstart script already created a device with the Unique ID you provided. You can verify its status there.

---

## Launch the /IOTCONNECT‐Enabled Demo

Once your three files are in `iotc_config/`, return to the project root and launch:

```bash
cd /var/rootdirs/opt/QCS6490-Vision-AI-Demo
sudo bash ./launch_visionai_with_env.sh
```

- You will see a 3‐second countdown. **Press “i”** during that interval to select `visionai-iotc.py` (the IoTConnect‐enabled demo).  
- If you do not press anything, the standard local demo (`visionai.py`) will run instead.
- Internally, `visionai-iotc.py` does:
  ```python
  DeviceConfig.from_iotc_device_config_json_file(
      device_config_json_path="iotc_config/iotcDeviceConfig.json",
      device_cert_path="iotc_config/device-cert.pem",
      device_pkey_path="iotc_config/device-pkey.pem"
  )
  self.iotc = Client(config=device_config, callbacks=Callbacks(command_cb=…))
  self.iotc.connect()
  ```
- Once connected, you should see console output similar to:
  ```
  [IOTCONNECT] Connecting to MQTT broker…
  [IOTCONNECT] Connected (ClientID: QCS6490-01)
  [IOTCONNECT] Sending initial telemetry…
  …
  ```

If all goes well, your VisionAI‐Kit is now online and communicating with /IOTCONNECT.

---

## Telemetry & Commands

After connecting, `visionai-iotc.py` will send telemetry every 5 seconds and listen for two commands: `start_demo` and `stop_demo`. Below is a summary of the fields and commands, plus how to test them in /IOTCONNECT.

### Telemetry Fields

Every 5 seconds, the demo gathers system metrics and publishes a JSON payload (all numeric):

- **cpu_usage** – CPU utilization (0 – 100)  
- **gpu_usage** – GPU utilization (0 – 100)  
- **memory_usage** – RAM utilization (0 – 100)  
- **cpu_temp** – CPU temperature (°C or sensor units)  
- **gpu_temp** – GPU temperature (°C or sensor units)  
- **memory_temp** – Memory temperature (°C or sensor units)  
- **critical** – A fixed threshold (set to 85)

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

> **Under the hood** (from `visionai-iotc.py`):
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
>
> You can confirm these fields under **Devices → Telemetry** in /IOTCONNECT.

---

### Supported Commands

The demo listens for two “device‐to‐cloud” commands (`start_demo`, `stop_demo`). When a command arrives, you’ll see a console log:

```
[IOTCONNECT] Command received: <command_name>
```

After performing its GUI update, the demo sends an acknowledgment back to /IOTCONNECT.

#### start_demo `<camera>` `<pipeline>`

- **Purpose**: Switch the specified camera (either `cam1` or `cam2`) to a new demo pipeline.  
- **Arguments**:
  1. `camera` – `cam1` or `cam2` (case‐insensitive)  
  2. `pipeline` – a string `"1"`–`"6"`, mapping to one of six demo modes.  
- **Behavior**:
  ```python
  camera = command.command_args[0].lower()
  pipeline = command.command_args[1].lower()
  pipeline_mapping = {"1":1, "2":2, "3":3, "4":4, "5":5, "6":6}
  pipeline_index = pipeline_mapping.get(pipeline)

  if camera == 'cam1':
      GLib.idle_add(self.eventHandler.demo_selection0.set_active, pipeline_index)
      ack_message = f"CAM1 started {pipeline}"
      ack_status = C2dAck.CMD_SUCCESS_WITH_ACK

  elif camera == 'cam2':
      GLib.idle_add(self.eventHandler.demo_selection1.set_active, pipeline_index)
      ack_message = f"CAM2 started {pipeline}"
      ack_status = C2dAck.CMD_SUCCESS_WITH_ACK

  else:
      raise ValueError(f"Invalid camera: {camera}")

  self.iotc.send_command_ack(command, ack_status, ack_message)
  ```
- **Example in /IOTCONNECT portal**:
  1. Go to **Devices → Devices**, click your device, go to **Commands → Send Command**.
  2. Set **Command name** = `start_demo`.  
  3. Set **Arguments** (JSON array) =  
     ```json
     ["cam1", "2"]
     ```
  4. Click **Submit**.
  5. On the VisionAI‐Kit console:
     ```
     [IOTCONNECT] Command received: start_demo
     Received command start_demo ['cam1','2']
     CAM1 started 2
     ```
  6. In the portal’s **Command Acknowledgments** section, you’ll see:
     - **Status**: `SUCCESS_WITH_ACK`  
     - **Message**: `"CAM1 started 2"`
  7. The GUI dropdown for Camera 1 switches to demo #2.

#### stop_demo `<camera>`

- **Purpose**: Stop the demo on the specified camera (sets its dropdown to “Off”).  
- **Arguments**:
  1. `camera` – `cam1` or `cam2` (case‐insensitive)  
- **Behavior**:
  ```python
  camera = command.command_args[0].lower()
  if camera == 'cam1':
      GLib.idle_add(self.eventHandler.demo_selection0.set_active, 0)
      ack_message = "CAM1 demo stopped"
      ack_status = C2dAck.CMD_SUCCESS_WITH_ACK

  elif camera == 'cam2':
      GLib.idle_add(self.eventHandler.demo_selection1.set_active, 0)
      ack_message = "CAM2 demo stopped"
      ack_status = C2dAck.CMD_SUCCESS_WITH_ACK

  else:
      raise ValueError(f"Invalid camera: {camera}")

  self.iotc.send_command_ack(command, ack_status, ack_message)
  ```
- **Example in /IOTCONNECT portal**:
  1. Go to **Devices → Devices**, click your device, go to **Commands → Send Command**.
  2. Set **Command name** = `stop_demo`.  
  3. Set **Arguments** =  
     ```json
     ["cam2"]
     ```
  4. Click **Submit**.
  5. On the VisionAI‐Kit console:
     ```
     [IOTCONNECT] Command received: stop_demo
     Received command stop_demo ['cam2']
     CAM2 demo stopped
     ```
  6. In **Command Acknowledgments**, you’ll see:
     - **Status**: `SUCCESS_WITH_ACK`  
     - **Message**: `"CAM2 demo stopped"`
  7. The GUI dropdown for Camera 2 reverts to index 0 (“Off”).

> **Under the hood**:
> ```python
> def handle_iotconnect_command(self, command):
>     cmd_name = command.command_name
>
>     if cmd_name == 'start_demo':
>         # (logic shown above)
>     elif cmd_name == 'stop_demo':
>         # (logic shown above)
>     else:
>         self.iotc.send_command_ack(command, C2dAck.CMD_FAILED, "Unknown command")
> ```

---

### How to Use Telemetry & Commands

1. **Confirm telemetry**:
   - In /IOTCONNECT portal, go to **Devices → Telemetry**, select your device.  
     You should see a JSON record appear every 5 seconds containing the fields above.
   - If you don’t see any telemetry:
     - Verify the device’s **Status** under **Devices → Devices** is “Active” (not “Disconnected”).
     - Ensure `device-cert.pem`, `device-pkey.pem`, and `iotcDeviceConfig.json` all exist in `iotc_config/`.
     - Check the VisionAI‐Kit console for errors (e.g., “TLS handshake failed” or “certificate unknown”).

2. **Send a command**:
   - In /IOTCONNECT portal: **Devices → Devices** → select your device → **Commands → Send Command**.
   - For `start_demo`, use arguments like `["cam1","3"]`.
   - For `stop_demo`, use arguments like `["cam2"]`.
   - Click **Submit**.  
   - Watch **Command Acknowledgments**:
     - **Status** should be `SUCCESS_WITH_ACK`.  
     - **Message** e.g. `"CAM1 started 3"`.  
   - On the VisionAI‐Kit’s GUI, the dropdown will switch or revert accordingly.

3. **Pipeline indices reference**:
   The pipelines `1–6` map to these dropdown options:
   ```
   0: Off
   1: AI Classification
   2: AI Object Detection
   3: AI Pose Estimation
   4: AI Semantic Segmentation
   5: GPU Stress Test
   6: Memory Benchmark
   ```

4. **Stopping a running demo**:
   Issue `stop_demo` with `["cam1"]` or `["cam2"]` to set that camera’s dropdown back to 0 (“Off”).

---

## Summary

- **Template**: We provided `iotconnect/tria_6490_device_template.JSON` in this repo. Import it under **Devices → Templates** as `TRIA Vision AI Kit 6490`.
- **Device Creation**: In /IOTCONNECT → **Devices → Devices**, click **Create Device**, fill out **Unique ID**, **Device Name**, **Entity**, select **Template** = `TRIA Vision AI Kit 6490`, choose **Auto‐generated certificate**, then **Save & View**.
- **Download Configuration**: From the Device Info page, click the **Download Device Configuration** icon. Unzip the resulting ZIP into `iotc_config/`, then `chmod 644` those files.
- **Launch Demo**: Run `sudo bash ./launch_visionai_with_env.sh` on the VisionAI‐Kit. Press **“i”** within 3 seconds to pick the IoTConnect demo (`visionai-iotc.py`).
- **Verify**:  
  - Under **Devices → Telemetry** you will see new telemetry every 5 seconds.  
  - Under **Devices → Commands**, send `start_demo`/`stop_demo` to switch demos on Camera 1 or 2.

Once you’ve completed these steps, your QCS6490 Vision AI Kit will connect to /IOTCONNECT automatically, start streaming telemetry, and respond to `start_demo`/`stop_demo` commands—no further manual copying of files is necessary.

---

## Links & References

- **TRIA 6490 Device Template JSON** (raw):  
  [https://raw.githubusercontent.com/mlamp99/QCS6490-Vision-AI-Demo/main/iotconnect/tria_6490_device_template.JSON](https://raw.githubusercontent.com/mlamp99/QCS6490-Vision-AI-Demo/main/iotconnect/tria_6490_device_template.JSON)
- **Avnet Official README** (for full context):  
  [https://github.com/Avnet/QCS6490-Vision-AI-Demo/blob/main/README.md](https://github.com/Avnet/QCS6490-Vision-AI-Demo/blob/main/README.md)
- **/IOTCONNECT Python Lite SDK** (only if you opt for script‐based provisioning):  
  [https://github.com/avnet-iotconnect/iotc-python-lite-sdk](https://github.com/avnet-iotconnect/iotc-python-lite-sdk)
- **Subscription Links**:  
  - AWS: `https://subscription.iotconnect.io/subscribe?cloud=aws`  
  - Azure: `https://subscription.iotconnect.io/subscribe?cloud=azure`

That’s it—follow these steps once, and your TRIA Vision AI Kit demo will be fully integrated with /IOTCONNECT.  