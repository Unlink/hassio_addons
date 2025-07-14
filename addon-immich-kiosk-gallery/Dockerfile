ARG BUILD_FROM=ghcr.io/hassio-addons/base:18.0.2

# hadolint ignore=DL3006
FROM ${BUILD_FROM}

# Copy root filesystem
COPY rootfs /

# Set execute permissions for s6-overlay scripts and binaries
RUN chmod +x /etc/s6-overlay/s6-rc.d/immich-kiosk/run && \
    chmod +x /etc/s6-overlay/s6-rc.d/immich-kiosk/finish && \
    chmod +x /usr/bin/immich_kiosk.py

# Setup base packages
RUN apk add --no-cache \
    coreutils=9.7-r1 \
    python3=3.12.8-r1 \
    py3-pip=24.3.1-r0 \
    py3-flask=3.0.3-r1 \
    py3-requests=2.32.3-r0

# Install additional Python packages
RUN pip3 install --no-cache-dir \
    flask-cors==4.0.0

# Build arguments
ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_DESCRIPTION
ARG BUILD_NAME
ARG BUILD_REF
ARG BUILD_REPOSITORY
ARG BUILD_VERSION

# Labels
LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="Michal Ďuračík" \
    org.opencontainers.image.title="${BUILD_NAME}" \
    org.opencontainers.image.description="${BUILD_DESCRIPTION}" \
    org.opencontainers.image.vendor="Michal Ďuračík" \
    org.opencontainers.image.authors="Michal Ďuračík" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://github.com/Unlink/hassio_addons" \
    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/main/README.md" \
    org.opencontainers.image.created=${BUILD_DATE} \
    org.opencontainers.image.revision=${BUILD_REF} \
    org.opencontainers.image.version=${BUILD_VERSION}
