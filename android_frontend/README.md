Android Frontend (Qt) - README

Overview

This folder contains a native Qt (C++) frontend scaffold that loads the existing QML UI from `../frontend/main.qml` and connects to an MQTT broker using Qt MQTT. The Python backend can run remotely (on a PC or server). This project is intended to be opened and built in Qt Creator using an Android kit.

Prerequisites

- Qt 6.6 or later with the following modules installed:
  - Qt Quick / QML
  - Qt MQTT (Qt6::Mqtt)
  - Qt Multimedia (optional, for local sound)
- Qt Creator with Android kits configured
- Android SDK and NDK matching your Qt version (check Qt docs for the recommended NDK version)
- JDK 11 or 17
- CMake 3.16+
- Ninja or other build tool

Suggested versions (known to work with Qt 6.6):
- Android SDK: latest (use SDK Manager)
- Android NDK: r25b (or Qt-recommended NDK)
- JDK: OpenJDK 11 or 17
- Qt: 6.6.x with Qt MQTT add-on

Quick desktop test (before building for Android)

1. Install Qt with Desktop kit and Qt MQTT.
2. Create a `build` directory and run CMake + build:

```powershell
cd android_frontend
mkdir build
cd build
cmake .. -G "Ninja"
cmake --build .
```

3. Run the generated binary from the build folder. It will load `../frontend/main.qml` (make sure you run from the project root so relative paths resolve).

Open in Qt Creator (Android)

1. Open `android_frontend/CMakeLists.txt` in Qt Creator.
2. Configure a kit for Android (Tools → Options → Devices → Android) and set the SDK/NDK/JDK paths.
3. Select the Android kit for the project and run `Configure`.
4. Build and Run — Qt Creator will produce an APK and deploy to a connected emulator or device.

Notes

- The scaffold expects an MQTT broker reachable at `localhost:1883`. For Android device testing, either run the broker on the same device (rare) or point the `TricorderBackend` in C++ to the host machine or a public broker. Use your machine IP address (e.g., 192.168.x.x) rather than `localhost` when the broker runs on a host machine.
- The C++ backend publishes acknowledgements to `tricorder/commands` (JSON). The Python backend can listen to that topic to stay in sync.

Next steps

- Replace the MQTT `localhost` hostname in `src/tricorderbackend.cpp` with a configurable setting or a UI field to enter broker address.
- Add signing and release configuration in Qt Creator for a production APK.
- Add multimedia/permissions handling (microphone) if implementing voice comms.

*** End README
