#!/command/with-contenv bashio
# shellcheck shell=bash
# ==============================================================================
# WMBus Meters Runner - WMBus reading script wrapper
# ==============================================================================

bashio::log.info "Starting WMBus meters reading..."

# Execute the Python script
if python3 /usr/bin/wmbus_read.py; then
    bashio::log.info "WMBus meters reading completed successfully"
else
    bashio::log.error "WMBus meters reading failed"
    exit 1
fi

lsusb