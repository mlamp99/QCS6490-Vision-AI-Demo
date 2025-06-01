## QCS6490 Vision AI Demo: /IOTCONNECT Quickstart

### Table of Contents

* [Introduction](#introduction)
* [Prerequisites](#prerequisites)
* [Cloud Account & Device Template Setup](#cloud-account--device-template-setup)
* [Device Setup & Certificate Provisioning](#device-setup--certificate-provisioning)
* [Download Device Configuration](#download-device-configuration)
* [Run Quickstart to Connect Device](#run-quickstart-to-connect-device)
* [Launch the /IOTCONNECT-Enabled Demo](#launch-the-iotconnect-enabled-demo)
* [Telemetry & Commands](#telemetry--commands)

  * [Telemetry Fields](#telemetry-fields)
  * [Supported Commands](#supported-commands)

    * [start\_demo `<camera>` `<pipeline>`](#start_demo-camera-pipeline)
    * [stop\_demo `<camera>`](#stop_demo-camera)
  * [How to Use Telemetry & Commands](#how-to-use-telemetry--commands)
* [Summary](#summary)
* [Links & References](#links--references)

---

## Introduction

This Quickstart guide walks you through:

1. Importing the **TRIA Vision AI Kit 6490** Device Template (provided in this repository).
2. Running the Quickstart script (`quickstart.py`) on the Vision AI Kit to generate device certificates and register/connect the device.
3. Creating a Device in /IOTCONNECT using that template, and pasting the generated certificate + private key PEM text into the portal.
4. Downloading the Device Configuration JSON from /IOTCONNECT.
5. Placing the certificate, private key, and JSON into `iotc_config/` so that `visionai-iotc.py` can use them.
6. Launching the Vision AI demo, which sends telemetry and accepts commands via /IOTCONNECT.

---

## Prerequisites

* A working **Bash shell** on your host machine (Linux or Windows with Git Bash).
* **`adb` (Android Debug Bridge)** installed on your host (to communicate with the Vision AI Kit via USB).

  * On Ubuntu: `sudo apt install android-tools-adb`
  * On Windows: download and install from [https://developer.android.com/studio/releases/platform-tools](https://developer.android.com/studio/releases/platform-tools).
* **Python 3** (3.6+) with `pip`.
* **`openssl`** CLI (optional, for inspecting certificates).
* **`curl`** or **`wget`** (for fetching files if needed).
* An active **/IOTCONNECT** subscription (AWS- or Azure-based). If you don’t already have one, sign up for a free trial:

  * AWS: `https://subscription.iotconnect.io/subscribe?cloud=aws`
  * Azure: `https://subscription.iotconnect.io/subscribe?cloud=azure`
* (Optional) If you previously installed the full IoTConnect Python SDK, create a separate virtual environment before installing the Lite SDK. The Lite SDK pins `paho-mqtt` to versions guaranteed to run with `visionai-iotc.py`.

---

## Cloud Account & Device Template Setup

Before creating a Device, you need a Device Template in /IOTCONNECT that matches exactly the telemetry attributes and commands the TRIA Vision AI Kit 6490 demo will send/receive.

#### 1. Download (or Clone) the TRIA 6490 Device Template JSON

We’ve already defined a complete template JSON in this repository. It includes:

* **Telemetry attributes**:
  `cpu_usage`, `gpu_usage`, `memory_usage`, `cpu_temp`, `gpu_temp`, `memory_temp`, `critical`
* **Commands**:
  `start_demo`, `stop_demo`

Use the file in [`iotconnect/tria_6490_device_template.JSON`](iotconnect/tria_6490_device_template.JSON).

> **Important**: Do not modify this file unless you need to add/remove telemetry fields or commands. If you do edit it, re-import it under a new Template Code.

#### 2. Import the TRIA Template into /IOTCONNECT

1. **Log in** to your /IOTCONNECT portal (AWS or Azure version).

2. In the left navigation menu, click **Devices → Templates**.

   ![Select “Templates”](iotconnect/images/select_template.png)

3. Click **Create Template** (top-right).

   ![Create Template](iotconnect/images/create_template.png)

4. In the “Create Template” page, click **Import** (top-right).

   ![Select “Import Template”](iotconnect/images/select_import_template.png)

5. **Upload** `tria_6490_device_template.JSON`

   * Once uploaded, click **Save**.
   * You should now see a new template named **TRIA Vision AI Kit 6490** in your Template list, with:

     * **Auth Type**: x509
     * **Message Version**: 2.1
     * **Attributes 7** (for the telemetry fields)
     * **Commands 2** (`start_demo`, `stop_demo`)

> **Tip**: If you ever need to tweak the template (for example, add a new telemetry field), select this template from the Template listing and use IOTCONNECT's GUI editor.

---

## Device Setup & Certificate Provisioning

Instead of manually generating certificates ahead of time, we’ll use the Quickstart flow to have /IOTCONNECT generate a certificate + private key. These will be used when creating the device in the portal.

1. **Ensure ADB is running** and the Vision AI Kit is connected over USB. On your host, verify:

   ```bash
   adb devices
   ```

   You should see a device ID corresponding to your Vision AI Kit.

2. **Create an `iotc_config/` folder** in your project (if not already present):

   ```bash
   mkdir -p iotc_config
   ```

3. **Copy `quickstart.sh` into `iotc_config/`** (it’s already included in this repo):

   ```bash
   cp iotc_config/quickstart.sh iotc_config/
   chmod +x iotc_config/quickstart.sh
   ```

4. **Push the Quickstart scripts to the device** via ADB:

   ```bash
   adb push iotc_config/quickstart.sh /data/local/tmp/
   ```

5. **Open a shell on the Vision AI Kit**:

   ```bash
   adb shell
   ```

6. **Install the Lite SDK** on-device (if not already installed):

   ```bash
   python3 -m pip install iotconnect-sdk-lite
   ```

   If Python/pip is not available, refer to your device’s documentation to enable the Python environment.

7. **Run the Quickstart script** on-device:

   ```bash
   cd /data/local/tmp
   ./quickstart.sh
   ```

   * The script will download `quickstart.py` to the same folder.
   * At the end, it will prompt you to run:

     ```
     python3 quickstart.py
     ```

8. **Execute `quickstart.py`** on-device:

   ```bash
   python3 quickstart.py
   ```

   * You should see output indicating MQTT connection success, e.g.

     ```
     Connected. Reason Code: Success
     MQTT connected (ClientID: QCS6490-01)
     > {"d":[{"d":{"sdk_version":"1.0.2","version":"1.0.0","random":29}}]}
     ```
   * At this point, the script will generate:

     * `device-cert.pem`
     * `device-pkey.pem`
     * `iotcDeviceConfig.json`
   * Push these files back to your host:

     ```bash
     adb pull /data/local/tmp/device-cert.pem iotc_config/
     adb pull /data/local/tmp/device-pkey.pem iotc_config/
     adb pull /data/local/tmp/iotcDeviceConfig.json iotc_config/
     ```
   * Exit ADB shell:

     ```bash
     exit
     ```

Now you have in your local `iotc_config/` folder the three files needed:

```
iotc_config/device-cert.pem
iotc_config/device-pkey.pem
iotc_config/iotcDeviceConfig.json
```

These will be used when creating the device in /IOTCONNECT.

> **Important**: The JSON (`iotcDeviceConfig.json`) contains fields like:
>
> ```json
> {
>   "ver": "2.1",
>   "pf": "aws",
>   "cpid": "------------------------------",
>   "env": "poc",
>   "uid": "QCS6490-01",
>   "did": "QCS6490-01",
>   "at": 3,
>   "disc": "https://awsdiscovery.iotconnect.io"
> }
> ```
>
> Use this JSON and the PEM files in the next step.

---

## Download Device Configuration

Now create the Device in the portal using the certificate you generated.

1. **Log in** to your /IOTCONNECT portal and navigate to **Devices → Devices**.

2. Click **Create Device** (top-right).

   ![Enter Device Certificate](iotconnect/images/enter_device_cert.png)

3. Fill out the form:

   * **Unique Id**: Must match the `uid` from `iotcDeviceConfig.json` (e.g. `QCS6490-01`).
   * **Device Name**: e.g. `QCS6490-VisionAI-Kit`.
   * **Entity**: Select your Entity (e.g. `Avnet`).
   * **Template**: Choose `TRIA Vision AI Kit 6490`.

4. Under **Device certificate**, choose **Use my certificate**.

   * In the **Device Certificate** upload, select `iotc_config/device-cert.pem` from your host.
   * In the **Certificate Authority** dropdown, select the CA that issued the Quickstart-generated cert.
   * In the **Certificate Text** box, paste the full contents of `iotc_config/device-cert.pem` (PEM-encoded).
   * For **Private Key**, select or paste the contents of `iotc_config/device-pkey.pem`.

5. Click **Save & View**.

6. On the Device Info page, click the **Download Device Configuration** icon to get the raw JSON (if needed).
   ![Download Device Configuration](iotconnect/images/download_device_config.png)

> At this point, the device is registered in /IOTCONNECT and has the correct certificate.

---

## Run Quickstart to Connect Device

If you haven’t already connected with `quickstart.py`, return to the Vision AI Kit and ensure the same three files are present on-device in `/data/local/tmp/`:

```bash
adb push iotc_config/device-cert.pem /data/local/tmp/
adb push iotc_config/device-pkey.pem /data/local/tmp/
adb push iotc_config/iotcDeviceConfig.json /data/local/tmp/
```

Then re-run:

```bash
adb shell
cd /data/local/tmp
python3 quickstart.py
exit
```

This will establish the MQTT connection under the registered device identity.

> **Note**: After running `quickstart.py`, you should see in /IOTCONNECT that the device’s status becomes “Active” (not “Disconnected”).

---

## Launch the /IOTCONNECT-Enabled Demo

With the device connected, run the Vision AI demo on-device so it streams telemetry and listens for commands.

1. Push the demo code to the device (if not already):

   ```bash
   adb push visionai-iotc.py /data/local/tmp/
   adb push launch_visionai_with_env.sh /data/local/tmp/
   ```

2. Open an ADB shell on the Vision AI Kit:

   ```bash
   adb shell
   cd /data/local/tmp
   chmod +x launch_visionai_with_env.sh
   sudo bash ./launch_visionai_with_env.sh
   ```

   * During the 3-second countdown, **press “i”** to select `visionai-iotc.py`.
   * If no key is pressed, it defaults to `visionai.py` (local demo).

3. Watch for console output:

   ```
   [IOTCONNECT] Connecting to MQTT broker…
   [IOTCONNECT] Connected (ClientID: QCS6490-01)
   [IOTCONNECT] Sending initial telemetry…
   …
   ```

Your Vision AI Kit is now online with /IOTCONNECT.

---

## Telemetry & Commands

Once connected, `visionai-iotc.py` sends telemetry every 5 seconds and listens for two commands: `start_demo` and `stop_demo`.

### Telemetry Fields

Each payload includes these numeric fields:

* **cpu\_usage** – CPU utilization (0 – 100)
* **gpu\_usage** – GPU utilization (0 – 100)
* **memory\_usage** – RAM utilization (0 – 100)
* **cpu\_temp** – CPU temperature (°C or sensor units)
* **gpu\_temp** – GPU temperature (°C or sensor units)
* **memory\_temp** – Memory temperature (°C or sensor units)
* **critical** – A fixed threshold (set to 85)

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
>
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

> You can confirm these fields under **Devices → Telemetry** in /IOTCONNECT.

---

### Supported Commands

The demo listens for two “device-to-cloud” commands (`start_demo`, `stop_demo`). When a command arrives, you’ll see a console log:

```
[IOTCONNECT] Command received: <command_name>
```

After performing its GUI update, the demo sends an acknowledgment back to /IOTCONNECT.

#### start\_demo `<camera>` `<pipeline>`

* **Purpose**: Switch the specified camera (either `cam1` or `cam2`) to a new demo pipeline.
* **Arguments**:

  1. `camera` – `cam1` or `cam2` (case-insensitive)
  2. `pipeline` – a string `"1"`–`"6"`, mapping to one of six demo modes.
* **Behavior**:

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
* **Example in /IOTCONNECT portal**:

  1. Go to **Devices → Devices**, click your device, then **Commands → Send Command**.
  2. Set **Command name** = `start_demo`.
  3. Set **Arguments** (JSON array) =

     ```json
     ["cam1", "2"]
     ```
  4. Click **Submit**.
  5. On-device console:

     ```
     [IOTCONNECT] Command received: start_demo
     Received command start_demo ['cam1','2']
     CAM1 started 2
     ```
  6. In the portal’s **Command Acknowledgments**, you’ll see:

     * **Status**: `SUCCESS_WITH_ACK`
     * **Message**: `"CAM1 started 2"`
  7. The GUI dropdown for Camera 1 switches to demo #2.

#### stop\_demo `<camera>`

* **Purpose**: Stop the demo on the specified camera (sets its dropdown to “Off”).
* **Arguments**:

  1. `camera` – `cam1` or `cam2` (case-insensitive)
* **Behavior**:

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
* **Example in /IOTCONNECT portal**:

  1. Go to **Devices → Devices**, click your device, then **Commands → Send Command**.
  2. Set **Command name** = `stop_demo`.
  3. Set **Arguments** =

     ```json
     ["cam2"]
     ```
  4. Click **Submit**.
  5. On-device console:

     ```
     [IOTCONNECT] Command received: stop_demo
     Received command stop_demo ['cam2']
     CAM2 demo stopped
     ```
  6. In **Command Acknowledgments**, you’ll see:

     * **Status**: `SUCCESS_WITH_ACK`
     * **Message**: `"CAM2 demo stopped"`
  7. The GUI dropdown for Camera 2 reverts to index 0 (“Off”).

> **Under the hood**:
>
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

   * In /IOTCONNECT portal, go to **Devices → Telemetry**, select your device. You should see a JSON record appear every 5 seconds containing the fields above.
   * If you don’t see any telemetry:

     * Verify the device’s **Status** under **Devices → Devices** is “Active” (not “Disconnected”).
     * Ensure `device-cert.pem`, `device-pkey.pem`, and `iotcDeviceConfig.json` all exist in `iotc_config/` on-device.
     * Check the Vision AI Kit console for errors (e.g., “TLS handshake failed”).

2. **Send a command**:

   * In /IOTCONNECT portal: **Devices → Devices** → select your device → **Commands → Send Command**.
   * For `start_demo`, use arguments like `["cam1","3"]`.
   * For `stop_demo`, use arguments like `["cam2"]`.
   * Click **Submit**.
   * Watch **Command Acknowledgments**:

     * **Status** should be `SUCCESS_WITH_ACK`.
     * **Message** e.g. `"CAM1 started 3"`.
   * On-device, the GUI dropdown will switch or revert accordingly.

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

* **Template**: We provided `iotconnect/tria_6490_device_template.JSON` in this repo. Import it under **Devices → Templates** as `TRIA Vision AI Kit 6490`.
* **Certificate Generation & Device Registration**: Run `quickstart.sh` on-device to generate `device-cert.pem`, `device-pkey.pem`, and `iotcDeviceConfig.json`.
* **Device Creation**: In /IOTCONNECT → **Devices → Devices** → **Create Device**, fill out form, choose **Use my certificate**, and paste/upload the generated PEMs.
* **Device Configuration**: Download the raw JSON if needed.
* **Connect Device**: Push the three files to-device and re-run `quickstart.py` to ensure MQTT connection.
* **Launch Demo**: Run `sudo bash ./launch_visionai_with_env.sh` on-device, press “i” within 3 seconds to pick `visionai-iotc.py`.
* **Verify**:

  * Under **Devices → Telemetry**, watch for telemetry every 5 seconds.
  * Under **Devices → Commands**, send `start_demo`/`stop_demo` to switch demos on Camera 1 or 2.

Once complete, your QCS6490 Vision AI Kit is fully integrated with /IOTCONNECT, streaming telemetry and responding to commands.

---

## Links & References

* **TRIA 6490 Device Template JSON** (raw):
  [https://raw.githubusercontent.com/mlamp99/QCS6490-Vision-AI-Demo/main/iotconnect/tria\_6490\_device\_template.JSON](https://raw.githubusercontent.com/mlamp99/QCS6490-Vision-AI-Demo/main/iotconnect/tria_6490_device_template.JSON)
* **Avnet Official README** (for full context):
  [https://github.com/Avnet/QCS6490-Vision-AI-Demo/blob/main/README.md](https://github.com/Avnet/QCS6490-Vision-AI-Demo/blob/main/README.md)
* **/IOTCONNECT Python Lite SDK** (only if you opt for script-based provisioning):
  [https://github.com/avnet-iotconnect/iotc-python-lite-sdk](https://github.com/avnet-iotconnect/iotc-python-lite-sdk)
* **Subscription Links**:

  * AWS: `https://subscription.iotconnect.io/subscribe?cloud=aws`
  * Azure: `https://subscription.iotconnect.io/subscribe?cloud=azure`
