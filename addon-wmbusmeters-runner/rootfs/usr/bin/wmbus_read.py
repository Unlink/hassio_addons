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
        # Check if device file exists
        if not os.path.exists(device_path):
            log_error(f"USB device {device_path} does not exist")
            return False
        
        # Check if device is accessible
        try:
            with open(device_path, 'r'):
                pass
        except PermissionError:
            log_error(f"Permission denied accessing {device_path}. Addon may need privileged access or USB device mapping.")
            return False
        except Exception as check_error:
            log_warning(f"Cannot access {device_path}: {check_error}")
        
        log_info(f"Resetting USB device: {device_path}")
        result = subprocess.run(["/usr/bin/usbreset", device_path], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            log_info(f"USB device {device_path} reset successful")
            if result.stdout:
                log_info(f"Reset output: {result.stdout.strip()}")
            return True
        else:
            log_error(f"USB device reset failed (exit code {result.returncode})")
            if result.stderr:
                log_error(f"Error details: {result.stderr.strip()}")
            if result.stdout:
                log_error(f"Output: {result.stdout.strip()}")
            
            # Provide helpful suggestions
            if "Operation not permitted" in result.stderr:
                log_error("SUGGESTION: Add 'privileged: [SYS_RAWIO, SYS_ADMIN]' and 'devices: [/dev/bus/usb]' to addon config")
            elif "No such file or directory" in result.stderr:
                log_error("SUGGESTION: Check if USB device is properly connected and detected by the system")
            
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


def check_usb_permissions():
    """Check if we have proper USB access permissions"""
    log_info("Checking USB permissions...")
    
    # Check if /dev/bus/usb exists
    if not os.path.exists("/dev/bus/usb"):
        log_warning("/dev/bus/usb does not exist - USB devices may not be accessible")
        return False
    
    # Try to list USB bus directories
    try:
        usb_buses = os.listdir("/dev/bus/usb")
        log_info(f"Found USB buses: {', '.join(usb_buses)}")
        
        # Check if we can access at least one device
        for bus in usb_buses:
            bus_path = f"/dev/bus/usb/{bus}"
            try:
                devices = os.listdir(bus_path)
                for device in devices:
                    device_path = f"{bus_path}/{device}"
                    if os.path.isfile(device_path):
                        # Try to access the device
                        try:
                            with open(device_path, 'r') as f:
                                log_info(f"Successfully accessed {device_path}")
                            return True
                        except PermissionError:
                            log_warning(f"Permission denied for {device_path}")
                        except Exception as e:
                            log_warning(f"Cannot access {device_path}: {e}")
            except PermissionError:
                log_warning(f"Permission denied listing {bus_path}")
                
        log_warning("No accessible USB devices found")
        return False
        
    except Exception as e:
        log_error(f"Failed to check USB permissions: {e}")
        return False


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
        
        # Check USB permissions first
        if not check_usb_permissions():
            log_warning("USB permission issues detected - device reset may fail")
            log_info("Consider adding 'privileged: [SYS_RAWIO, SYS_ADMIN]' and 'devices: [/dev/bus/usb]' to addon configuration")
        
        # Step 1: Reset USB devices matching filter
        if not reset_usb_devices(device_filter):
            log_error("Failed to reset some USB devices")
            # Don't exit here - continue with reading attempt
            log_info("Continuing with WMBus reading despite reset failures...")
        
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
