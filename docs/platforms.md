# Connecting to the box on each platform

🇫🇷 [Version française](fr/platforms.md)

The box is a Bluetooth **SPP** device: once paired, it is driven like a serial port.
Only the pairing step depends on the operating system.

## Windows ✅

1. Settings → Bluetooth → add the `RY-…` device.
2. Windows creates two COM ports (More Bluetooth settings → COM Ports):
   - **incoming** (e.g. COM5): do not use it;
   - **outgoing** "`JL_SPP`" (e.g. COM6): **this is the one**.
3. Open that port with any serial library (pyserial, .NET `SerialPort`, Win32
   `CreateFile`…).

Opening can take a few seconds (the radio link is being set up): in a GUI, open the
port outside the UI thread.

## Linux 🔍 (not tested)

```bash
bluetoothctl            # pair <MAC>, trust <MAC>
sdptool browse <MAC>    # find the RFCOMM channel of the JL_SPP service (often 1)
sudo rfcomm bind 0 <MAC> 1
# the port is /dev/rfcomm0
```

## macOS 🔍 (not tested)

After pairing, a `/dev/tty.<name>-…` port normally shows up for SPP devices.
Depending on the macOS version, it may not be created automatically.

## Android ✅ (method of the original app)

RFCOMM socket to the paired device with the standard SPP UUID, see
[`android/`](../android) (`SppDmxLink`). The `BLUETOOTH_CONNECT` runtime permission
is needed from Android 12 on.
