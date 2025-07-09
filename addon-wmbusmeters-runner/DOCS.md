# WMBus Meters Runner

Periodically runs WMBus meters reading with automatic USB device reset functionality.

## Features

- **Automatic USB device detection and reset** - Finds and resets USB devices before reading
- **Configurable reading interval** - Set how often to read meters (1-1440 minutes)  
- **Flexible device filtering** - Configure which USB devices to reset
- **Robust error handling** - Comprehensive logging and error recovery
- **Detailed USB diagnostics** - Comprehensive USB access and permission checking
- **Multiple reset methods** - Hardware reset with software fallbacks
- **s6-overlay integration** - Proper supervision and graceful shutdown

## Requirements

This addon requires direct USB device access to reset devices. The addon is configured with:

- **Full privileged access** (`privileged: true`)
- **USB device mapping** (`/dev/bus/usb`)
- **Full access mode** (`full_access: true`)
- **Disabled AppArmor** (`apparmor: false`)

## Configuration

### Basic Configuration

```yaml
log_level: info
reading_interval_minutes: 30
usb_device_filter: "RTL"
```

### Configuration Options

#### `log_level`
Controls the level of logging output.

- **Default**: `info`
- **Options**: `trace`, `debug`, `info`, `notice`, `warning`, `error`, `fatal`

#### `reading_interval_minutes`
How often to run the WMBus reading cycle.

- **Default**: `30`
- **Range**: 1-1440 minutes (1 minute to 24 hours)

#### `usb_device_filter`
Text to match in USB device descriptions for automatic reset.

- **Default**: `"DVB-T"`
- **Type**: String
- **Examples**: 
  - `"DVB-T"` - matches DVB-T devices
  - `"RTL2838"` - matches specific chip
  - `"Realtek"` - matches manufacturer
  - `"USB"` - matches any device with USB in description

## How It Works

1. **Service starts** and reads configuration
2. **Every configured interval**:
   - Scans USB devices with `lsusb`
   - Finds devices matching the filter
   - Resets matching devices using `usbreset`
   - Waits for devices to reinitialize
   - Runs WMBus reading logic
   - Logs results

## Usage Examples

### RTL-SDR Device
```yaml
usb_device_filter: "RTL2838"
reading_interval_minutes: 15
```

### Any Realtek Device
```yaml
usb_device_filter: "Realtek"
reading_interval_minutes: 60
```

### Custom Device
```yaml
usb_device_filter: "My Custom Device"
reading_interval_minutes: 5
```

## Troubleshooting

### USB Access Issues

If you encounter USB access problems, the addon provides detailed diagnostics:

1. **Check addon logs** - The addon performs comprehensive USB diagnostics on startup
2. **Run standalone diagnostics** - Access the addon container and run:
   ```bash
   python3 /usr/bin/usb_diagnostics.py
   ```

### Common Issues

#### Permission Denied
- Ensure the addon has `privileged: true` and `full_access: true`
- Check that `/dev/bus/usb` is mapped properly
- Verify AppArmor is disabled (`apparmor: false`)

#### USB Device Not Found
- Check that your device is connected and detected by the host
- Verify the `usb_device_filter` matches your device description
- Try different filter terms (e.g., "RTL", "DVB-T", "SDR")

#### Reset Failures
The addon uses multiple reset methods:
1. **Hardware reset** via `usbreset` utility
2. **Software reset** via sysfs
3. **Driver restart** via `modprobe` (for RTL devices)

### Multiple Reset Strategies

The addon automatically tries multiple approaches:
- Direct USB device reset using `usbreset`
- Sysfs-based device authorization toggle
- USB driver module restart for RTL-SDR devices
- Comprehensive error logging and fallback methods

## Logs

The addon provides detailed logging with timestamps:

```
[2025-01-09 10:30:00] INFO: WMBus Meters Runner starting...
[2025-01-09 10:30:00] INFO: Performing detailed USB access diagnostics...
[2025-01-09 10:30:00] INFO: Running with UID: 0 (root)
[2025-01-09 10:30:00] INFO: Using USB device filter: 'RTL'
[2025-01-09 10:30:00] INFO: Scanning for USB devices containing 'RTL'...
[2025-01-09 10:30:00] INFO: Found USB device: Realtek RTL2838 DVB-T at /dev/bus/usb/001/003
[2025-01-09 10:30:00] INFO: Found 1 device(s) matching 'RTL'
[2025-01-09 10:30:00] INFO: Attempting hardware reset for: /dev/bus/usb/001/003
[2025-01-09 10:30:00] INFO: USB device /dev/bus/usb/001/003 reset successful via usbreset
[2025-01-09 10:30:03] INFO: Starting WMBus meters reading...
[2025-01-09 10:30:03] INFO: WMBus Meters Runner completed successfully
```

## License
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.