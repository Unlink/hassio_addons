ARG BUILD_FROM=ghcr.io/hassio-addons/base:18.0.2


# Build stage for compiling usbreset
FROM alpine:3.19 AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers

# Copy and compile usbreset
COPY usbreset.c /tmp/usbreset.c
RUN gcc -o /tmp/usbreset /tmp/usbreset.c

# hadolint ignore=DL3006
FROM ${BUILD_FROM}

# Copy root filesystem
COPY rootfs /

# Copy compiled binary from builder stage
COPY --from=builder /tmp/usbreset /usr/bin/usbreset

# Set execute permissions for s6-overlay scripts and binaries
RUN chmod +x /etc/s6-overlay/s6-rc.d/wmbus-reader/run && \
    chmod +x /etc/s6-overlay/s6-rc.d/wmbus-reader/finish && \
    chmod +x /usr/bin/wmbus_read.sh && \
    chmod +x /usr/bin/usbreset

# Setup base
RUN apk add --no-cache \
    coreutils=9.7-r1

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
