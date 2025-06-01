## QCS6490 Vision AI Demo: /IOTCONNECT Quickstart

### Table of Contents

* [Introduction](#introduction)
* [Prerequisites](#prerequisites)
* [Cloud Account & Device Template Setup](#cloud-account--device-template-setup)
* [Project Layout](#project-layout)
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
2. Creating a Device in /IOTCONNECT using that template, and entering your device certificate.
3. Downloading the Device Configuration JSON from /IOTCONNECT.
4. Running the Quickstart script (`quickstart.py`) on the Vision AI Kit to register/connect the device.
5. Placing the resulting certificate and config files into `iotc_config/` so that `visionai-iotc.py` can use them.
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

## Project Layout

Your local project structure should now look like this (on your host machine after cloning or downloading):

```
QCS6490-Vision-AI-Demo  <-- your project root
├── visionai.py
├── visionai-iotc.py
├── launch_visionai_with_env.sh
├── iotc_config/              ← will hold certificate and JSON
│   └── quickstart.sh         ← (downloads & runs quickstart.py)
├── iotconnect/
│   ├── images/               ← contains the screenshots below
│   │   ├── select_template.png
│   │   ├── create_template.png
│   │   ├── select_import_template.png
│   │   ├── enter_device_cert.png
│   │   └── download_device_config.png
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

So **before** running the IoTConnect variant of the demo, you must have in `iotc_config/`:

```
device-cert.pem
device-pkey.pem
iotcDeviceConfig.json
```

---

## Device Setup & Certificate Provisioning

You must create your Device in /IOTCONNECT **and** provide a device certificate. You have these options for provisioning:

* **Option 1: Use your own existing certificate/key pair**
* **Option 2: Let /IOTCONNECT generate a certificate/key pair**

> **Note**: Whichever option you choose, you will need to place the PEM-encoded certificate text (and corresponding private key) into the Device Creation form, then click **Save & View**. After saving, you will download the Device Configuration (JSON) containing the IoTConnect endpoint details.

Below is how to proceed with either option:

#### 1. Open the “Create Device” form

1. In the /IOTCONNECT portal, navigate to **Devices → Devices**.

2. Click **Create Device** (top-right).

   ![Create Device Form](iotconnect/images/enter_device_cert.png)

3. Fill out the form:

   * **Unique Id**: A short, unique identifier (e.g. `QCS6490-01`).
   * **Device Name**: e.g. `QCS6490-VisionAI-Kit`.
   * **Entity**: Select your Entity (e.g. `Avnet`).
   * **Template**: Choose `TRIA Vision AI Kit 6490` (the template you imported).

4. Under **Device certificate**, choose **Use my certificate** (we will paste PEM text).

   * If you already have a certificate/key pair (Option 1), click **Browse** next to “Device Certificate” and upload your `device-cert.pem`.
   * If you want /IOTCONNECT to generate them (Option 2), click **Browse** anyway and upload a placeholder file, or simply paste a minimal PEM header (e.g. `-----BEGIN CERTIFICATE-----\n...`).

5. Under **Certificate Authority**, select the CA that issued your certificate (for Option 1). If you let /IOTCONNECT generate (Option 2), pick the default CA listed.

6. In the large **Certificate Text** box, paste the **PEM-encoded certificate** (the entire contents of `device-cert.pem`).

   > **Important**: If you let /IOTCONNECT generate certificates, you will retrieve the newly issued certificate later via Quickstart. In that case, paste the generated PEM text here.

7. In **Notes**, optionally add `Vision AI Demo – QCS6490`.

8. Click **Save & View**.

---

## Download Device Configuration

Once you click **Save & View**, you’ll be taken to the Device Info page. Now you need to download the **Device Configuration** (JSON):

1. On the Device Info page, click the **Download Device Configuration** icon (raw JSON icon).

   ![Download Device Configuration](iotconnect/images/download_device_config.png)

2. A window will pop up displaying the **raw JSON** (you will also get a ZIP if you had auto-generated certs). The JSON looks similar to:

   ```json
   {
     "ver": "2.1",
     "pf": "aws",
     "cpid": "------------------------------",
     "env": "poc",
     "uid": "QCS6490-01",
     "did": "QCS6490-01",
     "at": 3,
     "disc": "https://awsdiscovery.iotconnect.io"
   }
   ```

3. **Copy** the entire JSON text and save it into a local file called `iotcDeviceConfig.json` under your `iotc_config/` folder:

   ```bash
   mkdir -p iotc_config
   cat <<EOF > iotc_config/iotcDeviceConfig.json
   {  <paste the JSON here>  }
   EOF
   ```

4. If you already have a PEM certificate (Option 1), also copy your `device-cert.pem` and `device-pkey.pem` into `iotc_config/`:

   ```bash
   cp /path/to/your/device-cert.pem /path/to/your/device-pkey.pem iotc_config/
   chmod 644 iotc_config/device-cert.pem iotc_config/device-pkey.pem iotc_config/iotcDeviceConfig.json
   ```

5. If you selected **Option 2** (have /IOTCONNECT generate certs), you should have downloaded a ZIP containing `device-cert.pem`, `device-pkey.pem`, and `iotcDeviceConfig.json`.

   * **Unzip** those files into `iotc_config/` and set permissions:

     ```bash
     unzip ~/Downloads/QCS6490-01_iotc_config.zip -d /path/to/QCS6490-Vision-AI-Demo/iotc_config/
     chmod 644 iotc_config/device-cert.pem iotc_config/device-pkey.pem iotc_config/iotcDeviceConfig.json
     ```

At this point, you have in `iotc_config/`:

```
device-cert.pem

device-pkey.pem

iotcDeviceConfig.json
```

The certificate and JSON are now ready for the demonstration.

---

## Run Quickstart to Connect Device

Next, you must register/connect the Vision AI Kit with /IOTCONNECT so it can send telemetry. We provide a **Quickstart** script that uses these three files to establish an MQTT connection.

1. **Ensure ADB is running** and the Vision AI Kit is connected over USB. On your host, verify:

   ```bash
   adb devices
   ```

   You should see a device ID corresponding to your Vision AI Kit.

2. **Copy `quickstart.sh` into `iotc_config/`** (it’s already included in this repo).

   ```bash
   cp iotc_config/quickstart.sh iotc_config/
   chmod +x iotc_config/quickstart.sh
   ```

3. **Push the certificate and JSON files to the device** via ADB, so `quickstart.py` can access them locally:

   ```bash
   adb push iotc_config/device-cert.pem /data/local/tmp/
   adb push iotc_config/device-pkey.pem /data/local/tmp/
   adb push iotc_config/iotcDeviceConfig.json /data/local/tmp/
   adb push iotc_config/quickstart.sh /data/local/tmp/
   ```

4. **Open a shell on the Vision AI Kit**:

   ```bash
   adb shell
   ```

5. **Install the Lite SDK** on-device (if not already installed):

   ```bash
   python3 -m pip install iotconnect-sdk-lite
   ```

   If Python/pip is not available, refer to your device’s documentation to enable the Python environment.

6. **Run the Quickstart script** on-device:

   ```bash
   cd /data/local/tmp
   ./quickstart.sh
   ```

   * The script will download `quickstart.py` to the same folder.
   * At the end, it will prompt:

     ```
     The Quickstart setup is complete.
     You can now run this command on the command line to execute the Quickstart demo:
     python3 quickstart.py
     ```

7. **Execute `quickstart.py`** on-device:

   ```bash
   python3 quickstart.py
   ```

   * You should see output indicating MQTT connection success, e.g.:

     ```
     Connected. Reason Code: Success
     MQTT connected (ClientID: QCS6490-01)
     > {"d":[{"d":{"sdk_version":"1.0.2","version":"1.0.0","random":29}}]}
     ```

8. **Exit ADB shell** when done:

   ```bash
   exit
   ```

At this point, your Vision AI Kit is connected to /IOTCONNECT and ready to send telemetry.

> **Note**: If you ever need to re-run Quickstart, re-push the three files (`device-cert.pem`, `device-pkey.pem`, `iotcDeviceConfig.json`) via ADB and re-run `quickstart.sh` on-device.

---

## Launch the /IOTCONNECT-Enabled Demo

With the device connected, you can now run the Vision AI demo that streams telemetry and listens for commands.

1. **Push the demo code** (if not already on-device) and navigate to its folder:

   ```bash
   adb push visionai-iotc.py /data/local/tmp/
   adb push launch_visionai_with_env.sh /data/local/tmp/
   adb shell
   cd /data/local/tmp
   ```

2. **Execute the launcher script**:

   ```bash
   chmod +x launch_visionai_with_env.sh
   sudo bash ./launch_visionai_with_env.sh
   ```

   * A 3-second countdown appears. **Press “i”** to select the IoTConnect-enabled demo (`visionai-iotc.py`).
   * If you don’t press “i”, it defaults to the local demo (`visionai.py`).

3. **Observe output**:

   ```
   [IOTCONNECT] Connecting to MQTT broker…
   [IOTCONNECT] Connected (ClientID: QCS6490-01)
   [IOTCONNECT] Sending initial telemetry…
   …
   ```

If you see those lines, your Vision AI Kit is now online with /IOTCONNECT.

---

## Telemetry & Commands

Once connected, `visionai-iotc.py` sends telemetry every 5 seconds and listens for two commands: `start_demo` and `stop_demo`.

### Telemetry Fields

Every 5 seconds, the demo gathers system metrics and publishes a JSON payload (all numeric):

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
  7. The GUI dropdown for Camera 1 switches to demo #2.

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
  7. The GUI dropdown for Camera 2 reverts to index 0 (“Off”).

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

   * In /IOTCONNECT portal, go to **Devices → Telemetry**, select your device. You should see a JSON record appear every 5 seconds containing the fields above.
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
   Issue `stop_demo` with `["cam1"]` or `["cam2"]` to set that camera’s dropdown back to 0 (“Off”).

---

## Summary

* **Template**: We provided `iotconnect/tria_6490_device_template.JSON` in this repo. Import it under **Devices → Templates** as `TRIA Vision AI Kit 6490`.
* **Device Creation & Certificate**: In /IOTCONNECT → **Devices → Devices** → **Create Device**, fill out the form, choose **Use my certificate**, paste your PEM-encoded certificate (or a placeholder for generation), then **Save & View**.
* **Download Configuration**: On the Device Info page, click **Download Device Configuration**, copy the raw JSON into `iotc_config/iotcDeviceConfig.json`, and ensure `device-cert.pem` & `device-pkey.pem` are also in `iotc_config/`.
* **Connect Device**: Use `adb` from your PC to push those three files to `/data/local/tmp/` on the Vision AI Kit, then run `quickstart.sh` and `quickstart.py` on-device to establish the MQTT connection.
* **Launch Demo**: `sudo bash ./launch_visionai_with_env.sh` on-device, press “i” within 3 seconds to pick `visionai-iotc.py`.
* **Verify**:

  * Under **Devices → Telemetry**, watch for telemetry every 5 seconds.
  * Under **Devices → Commands**, send `start_demo`/`stop_demo` to switch demos on Camera 1 or 2.

Your QCS6490 Vision AI Kit will now connect to /IOTCONNECT automatically, start streaming telemetry, and respond to `start_demo`/`stop_demo` commands.

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
