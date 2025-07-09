# WMBus Meters Runner

Periodically runs WMBus meters reading with automatic USB device reset functionality.

## Features

- **Automatic USB device detection and reset** - Finds and resets USB devices before reading
- **Configurable reading interval** - Set how often to read meters (1-1440 minutes)  
- **Flexible device filtering** - Configure which USB devices to reset
- **Robust error handling** - Comprehensive logging and error recovery
- **USB permission diagnostics** - Automatically checks and reports USB access issues
- **s6-overlay integration** - Proper supervision and graceful shutdown

## Requirements

This addon requires direct USB device access to reset devices. You need to:

1. **Enable privileged access** for USB operations
2. **Map USB devices** to the container

## Configuration

### Required Configuration

```yaml
privileged:
  - SYS_RAWIO      # Required for USB device reset
  - SYS_ADMIN      # Required for low-level USB operations
devices:
  - /dev/bus/usb   # Maps USB devices to container
```

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

## Logs

The addon provides detailed logging with timestamps:

```
[2025-01-09 10:30:00] INFO: WMBus Meters Runner starting...
[2025-01-09 10:30:00] INFO: Using USB device filter: 'DVB-T'
[2025-01-09 10:30:00] INFO: Scanning for USB devices containing 'DVB-T'...
[2025-01-09 10:30:00] INFO: Found USB device: Realtek DVB-T USB Device at /dev/bus/usb/001/003
[2025-01-09 10:30:00] INFO: Found 1 device(s) matching 'DVB-T'
[2025-01-09 10:30:00] INFO: Resetting USB device: /dev/bus/usb/001/003
[2025-01-09 10:30:00] INFO: USB device /dev/bus/usb/001/003 reset successful
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