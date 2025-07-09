#!/usr/bin/env python3
"""
WMBus Meters Runner - Main reading script
Automatically finds and resets USB devices, then reads WMBus meters
"""

import subprocess
import sys
import re
import json
import os
from datetime import datetime


def log_info(message):
    """Log info message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] INFO: {message}", flush=True)


def log_error(message):
    """Log error message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ERROR: {message}", file=sys.stderr, flush=True)


def log_warning(message):
    """Log warning message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] WARNING: {message}", flush=True)


def get_config():
    """Read addon configuration from /data/options.json"""
    try:
        with open('/data/options.json', 'r') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        log_error(f"Invalid configuration file: {e}")
        return None
    except Exception as e:
        log_error(f"Failed to read configuration: {e}")
        return None


def find_usb_devices():
    """Find all USB devices using lsusb"""
    try:
        device_re = re.compile(r"Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<id>\w+:\w+)\s(?P<tag>.+)$", re.I)

        df = subprocess.check_output(["lsusb"], universal_newlines=True)
        devices = []
        
        for line in df.strip().split('\n'):
            if line.strip():
                match = device_re.match(line)
                if match:
                    info = match.groupdict()
                    info['device_path'] = f"/dev/bus/usb/{info['bus'].zfill(3)}/{info['device'].zfill(3)}"
                    devices.append(info)
        
        return devices
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to list USB devices: {e}")
        return []
    except Exception as e:
        log_error(f"Unexpected error while listing USB devices: {e}")
        return []


def reset_usb_device(device_path):
    """Reset USB device using usbreset utility"""
    try:
        log_info(f"Resetting USB device: {device_path}")
        result = subprocess.run(["/usr/bin/usbreset", device_path], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            log_info(f"USB device {device_path} reset successful")
            return True
        else:
            log_error(f"USB device reset failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        log_error("usbreset utility not found at /usr/bin/usbreset")
        return False
    except Exception as e:
        log_error(f"Failed to reset USB device {device_path}: {e}")
        return False


def reset_usb_devices(device_filter):
    """Find and reset USB devices matching the filter"""
    log_info(f"Scanning for USB devices containing '{device_filter}'...")
    devices = find_usb_devices()

    for device in devices:
        log_info(f"Found USB device: {device['tag']} at {device['device_path']}")
    
    filtered_devices = [d for d in devices if device_filter in d.get("tag", "")]
    
    if not filtered_devices:
        log_info(f"No devices containing '{device_filter}' found")
        return True
    
    log_info(f"Found {len(filtered_devices)} device(s) matching '{device_filter}'")
    
    success = True
    for device in filtered_devices:
        log_info(f"Found matching device: {device['tag']} at {device['device_path']}")
        if not reset_usb_device(device['device_path']):
            success = False
    
    if success:
        log_info("Waiting 3 seconds for devices to reinitialize...")
        import time
        time.sleep(3)
    
    return success


def read_wmbus_meters():
    log_info("Starting WMBus meters reading...")
    
    return True


def main():
    """Main function"""
    log_info("WMBus Meters Runner starting...")
    
    try:
        # Read configuration
        config = get_config()
        if config is None:
            log_error("Failed to load configuration")
            return 1
        
        device_filter = config.get("usb_device_filter", "DVB-T")
        log_info(f"Using USB device filter: '{device_filter}'")
        
        # Step 1: Reset USB devices matching filter
        if not reset_usb_devices(device_filter):
            log_error("Failed to reset some USB devices")
            return 1
        
        # Step 2: Read WMBus meters
        if not read_wmbus_meters():
            log_error("Failed to read WMBus meters")
            return 1
        
        log_info("WMBus Meters Runner completed successfully")
        return 0
        
    except KeyboardInterrupt:
        log_warning("Operation interrupted by user")
        return 130
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
