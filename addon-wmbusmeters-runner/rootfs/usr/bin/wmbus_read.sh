#!/command/with-contenv bashio
# shellcheck shell=bash
# ==============================================================================
# WMBus Meters Runner - WMBus reading script
# ==============================================================================

bashio::log.info "Starting WMBus meters reading..."

# Reset USB device before reading (if needed)
# USB_DEVICE="/dev/bus/usb/001/002"  # Adjust to your device
# if [[ -e "${USB_DEVICE}" ]]; then
#     bashio::log.info "Resetting USB device ${USB_DEVICE}..."
#     if /usr/bin/usbreset "${USB_DEVICE}"; then
#         bashio::log.info "USB device reset successful"
#         sleep 2  # Wait for device to reinitialize
#     else
#         bashio::log.warning "USB device reset failed"
#     fi
# fi

# TODO: Add your wmbus meters reading logic here
# Example: call wmbusmeters addon or direct wmbusmeters command

bashio::log.info "WMBus meters reading completed."

lsusb