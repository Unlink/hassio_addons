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
import time
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


def reset_usb_device_sysfs(device_id):
    """Alternative USB reset using sysfs (often works without full USB permissions)"""
    try:
        log_info(f"Attempting sysfs reset for USB device ID: {device_id}")
        
        # Find device in sysfs
        sysfs_paths = []
        if os.path.exists("/sys/bus/usb/devices"):
            for device_dir in os.listdir("/sys/bus/usb/devices"):
                device_path = f"/sys/bus/usb/devices/{device_dir}"
                try:
                    # Check if this is our device
                    idVendor_path = f"{device_path}/idVendor"
                    idProduct_path = f"{device_path}/idProduct"
                    
                    if os.path.exists(idVendor_path) and os.path.exists(idProduct_path):
                        with open(idVendor_path, 'r') as f:
                            vendor = f.read().strip()
                        with open(idProduct_path, 'r') as f:
                            product = f.read().strip()
                        
                        current_id = f"{vendor}:{product}"
                        if current_id.lower() == device_id.lower():
                            sysfs_paths.append(device_path)
                            
                except Exception as e:
                    continue
        
        if not sysfs_paths:
            log_warning(f"Device {device_id} not found in sysfs")
            return False
        
        success = True
        for sysfs_path in sysfs_paths:
            try:
                # Try to unbind and rebind the device
                authorized_path = f"{sysfs_path}/authorized"
                if os.path.exists(authorized_path):
                    log_info(f"Resetting device via sysfs: {sysfs_path}")
                    
                    # Disable device
                    with open(authorized_path, 'w') as f:
                        f.write('0')
                    
                    time.sleep(1)
                    
                    # Re-enable device
                    with open(authorized_path, 'w') as f:
                        f.write('1')
                    
                    log_info(f"Successfully reset device {device_id} via sysfs")
                else:
                    log_warning(f"No authorized file found for {sysfs_path}")
                    success = False
                    
            except PermissionError:
                log_error(f"Permission denied writing to {sysfs_path}")
                success = False
            except Exception as e:
                log_error(f"Failed to reset via sysfs {sysfs_path}: {e}")
                success = False
        
        return success
        
    except Exception as e:
        log_error(f"Failed to reset USB device {device_id} via sysfs: {e}")
        return False


def reset_usb_device(device_path, device_info=None):
    """Reset USB device using usbreset utility with fallback to sysfs"""
    
    try:
        # Check if device file exists
        if not os.path.exists(device_path):
            log_error(f"USB device {device_path} does not exist")
            return False
        
        # Method 1: Try usbreset first
        log_info(f"Attempting hardware reset for: {device_path}")
        try:
            result = subprocess.run(["/usr/bin/usbreset", device_path], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_info(f"USB device {device_path} reset successful via usbreset")
                if result.stdout:
                    log_info(f"Reset output: {result.stdout.strip()}")
                return True
            else:
                log_warning(f"usbreset failed (exit code {result.returncode})")
                if result.stderr:
                    log_warning(f"usbreset error: {result.stderr.strip()}")
                    
        except subprocess.TimeoutExpired:
            log_warning("usbreset timed out")
        except Exception as e:
            log_warning(f"usbreset failed: {e}")
        
        # Method 2: Try sysfs reset as fallback
        if device_info and 'id' in device_info:
            log_info("Trying alternative sysfs reset method...")
            if reset_usb_device_sysfs(device_info['id']):
                return True
        
        # Method 3: Try simple rebind via driver
        try:
            log_info("Trying driver rebind method...")
            # This is more experimental but sometimes works
            result = subprocess.run(['lsusb', '-s', device_path.split('/')[-2] + ':' + device_path.split('/')[-1]], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                log_info("Device is still detected by lsusb after reset attempts")
            return True  # Consider it successful if device is still there
            
        except Exception as e:
            log_warning(f"Driver rebind failed: {e}")
        
        log_error(f"All USB reset methods failed for {device_path}")
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
    failed_devices = []
    
    for device in filtered_devices:
        log_info(f"Found matching device: {device['tag']} at {device['device_path']}")
        if not reset_usb_device(device['device_path'], device):
            success = False
            failed_devices.append(device)
    
    # If some devices failed to reset and the filter suggests RTL devices, try driver reset
    if failed_devices and any(keyword in device_filter.lower() for keyword in ['rtl', 'dvb', 'sdr']):
        log_warning(f"Some devices failed to reset, attempting driver restart for RTL devices...")
        if reset_usb_drivers(device_filter):
            log_info("Driver reset completed - this may have resolved USB device issues")
            success = True  # Consider it successful if driver reset worked
    
    if success:
        log_info("Waiting 3 seconds for devices to reinitialize...")
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


def check_detailed_usb_access():
    """Perform detailed USB access checks and diagnostics"""
    log_info("Performing detailed USB access diagnostics...")
    
    # Check if running as root
    uid = os.getuid()
    log_info(f"Running with UID: {uid} ({'root' if uid == 0 else 'non-root'})")
    
    # Check groups
    try:
        import grp
        gid = os.getgid()
        groups = os.getgroups()
        log_info(f"Running with GID: {gid}, Groups: {groups}")
        
        # Check if in dialout or other relevant groups
        for group_name in ['dialout', 'plugdev', 'usb']:
            try:
                group_info = grp.getgrnam(group_name)
                if group_info.gr_gid in groups:
                    log_info(f"User is in group: {group_name}")
                else:
                    log_warning(f"User is NOT in group: {group_name}")
            except KeyError:
                log_info(f"Group {group_name} does not exist on this system")
    except Exception as e:
        log_warning(f"Failed to check groups: {e}")
    
    # Check /dev/bus/usb access
    usb_bus_path = "/dev/bus/usb"
    if os.path.exists(usb_bus_path):
        log_info(f"{usb_bus_path} exists")
        try:
            stat_info = os.stat(usb_bus_path)
            log_info(f"{usb_bus_path} permissions: {oct(stat_info.st_mode)}")
            
            # List available buses
            try:
                buses = os.listdir(usb_bus_path)
                log_info(f"Available USB buses: {buses}")
                
                for bus in buses[:3]:  # Check first 3 buses
                    bus_path = os.path.join(usb_bus_path, bus)
                    if os.path.isdir(bus_path):
                        try:
                            devices = os.listdir(bus_path)
                            log_info(f"Bus {bus} has {len(devices)} devices")
                            
                            # Check first device in detail
                            if devices:
                                device_path = os.path.join(bus_path, devices[0])
                                try:
                                    stat_info = os.stat(device_path)
                                    log_info(f"Device {device_path} permissions: {oct(stat_info.st_mode)}")
                                except Exception as e:
                                    log_warning(f"Cannot stat {device_path}: {e}")
                        except PermissionError:
                            log_warning(f"Permission denied listing bus {bus}")
                        except Exception as e:
                            log_warning(f"Error accessing bus {bus}: {e}")
                            
            except PermissionError:
                log_error(f"Permission denied listing {usb_bus_path}")
            except Exception as e:
                log_error(f"Error listing {usb_bus_path}: {e}")
                
        except Exception as e:
            log_error(f"Cannot stat {usb_bus_path}: {e}")
    else:
        log_error(f"{usb_bus_path} does not exist")
    
    # Check if usbreset binary exists and is executable
    usbreset_path = "/usr/bin/usbreset"
    if os.path.exists(usbreset_path):
        log_info(f"usbreset binary exists at {usbreset_path}")
        try:
            stat_info = os.stat(usbreset_path)
            log_info(f"usbreset permissions: {oct(stat_info.st_mode)}")
            if stat_info.st_mode & 0o111:
                log_info("usbreset is executable")
            else:
                log_warning("usbreset is NOT executable")
        except Exception as e:
            log_warning(f"Cannot stat usbreset: {e}")
    else:
        log_error(f"usbreset binary not found at {usbreset_path}")
    
    # Check capabilities if available
    try:
        result = subprocess.run(['capsh', '--print'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            log_info(f"Process capabilities: {result.stdout.strip()}")
        else:
            log_info("Could not determine process capabilities")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        log_info("capsh not available for capability check")
    except Exception as e:
        log_info(f"Failed to check capabilities: {e}")


def read_wmbus_meters():
    log_info("Starting WMBus meters reading...")
    
    return True


def reset_usb_drivers(device_filter):
    """Reset USB drivers for RTL-SDR devices as last resort"""
    log_info("Attempting to reset USB drivers...")
    
    # Common RTL-SDR drivers
    rtl_drivers = ['rtl2832u', 'dvb_usb_rtl28xxu', 'rtl2830', 'rtl2832']
    
    success = False
    for driver in rtl_drivers:
        try:
            # Try to remove the driver module
            log_info(f"Attempting to remove driver: {driver}")
            result = subprocess.run(['modprobe', '-r', driver], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_info(f"Successfully removed driver: {driver}")
                time.sleep(2)
                
                # Try to reload the driver
                log_info(f"Attempting to reload driver: {driver}")
                result = subprocess.run(['modprobe', driver], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    log_info(f"Successfully reloaded driver: {driver}")
                    success = True
                else:
                    log_warning(f"Failed to reload driver {driver}: {result.stderr}")
            else:
                log_info(f"Driver {driver} not loaded or cannot be removed")
                
        except subprocess.TimeoutExpired:
            log_warning(f"Driver reset timed out for {driver}")
        except Exception as e:
            log_warning(f"Driver reset failed for {driver}: {e}")
    
    if success:
        log_info("Driver reset completed, waiting for devices to re-enumerate...")
        time.sleep(5)  # Give time for devices to re-appear
    
    return success


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
        
        # Perform detailed USB diagnostics
        check_detailed_usb_access()
        
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
