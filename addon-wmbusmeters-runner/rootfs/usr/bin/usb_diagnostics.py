#!/usr/bin/env python3
"""
USB Diagnostics Script for WMBus Meters Runner
Standalone diagnostics tool to check USB access and permissions
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

def main():
    """Run comprehensive USB diagnostics"""
    log_info("Starting USB Diagnostics...")
    log_info("=" * 60)
    
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
    
    log_info("-" * 60)
    
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
                                    
                                    # Try to open the device
                                    try:
                                        with open(device_path, 'rb') as f:
                                            log_info(f"Successfully opened {device_path} for reading")
                                    except PermissionError:
                                        log_error(f"Permission denied opening {device_path}")
                                    except Exception as e:
                                        log_warning(f"Cannot open {device_path}: {e}")
                                        
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
    
    log_info("-" * 60)
    
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
    
    log_info("-" * 60)
    
    # Check lsusb
    try:
        log_info("Running lsusb to list USB devices...")
        result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            log_info(f"lsusb found {len(lines)} USB devices:")
            for line in lines:
                log_info(f"  {line}")
        else:
            log_error(f"lsusb failed: {result.stderr}")
    except Exception as e:
        log_error(f"Failed to run lsusb: {e}")
    
    log_info("-" * 60)
    
    # Check capabilities if available
    try:
        result = subprocess.run(['capsh', '--print'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            log_info(f"Process capabilities:")
            for line in result.stdout.strip().split('\n'):
                log_info(f"  {line}")
        else:
            log_info("Could not determine process capabilities")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        log_info("capsh not available for capability check")
    except Exception as e:
        log_info(f"Failed to check capabilities: {e}")
    
    log_info("=" * 60)
    log_info("USB Diagnostics completed.")

if __name__ == "__main__":
    main()
