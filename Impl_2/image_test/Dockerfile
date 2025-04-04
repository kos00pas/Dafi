FROM ubuntu:22.04

# === Setup basic build env ===
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    ninja-build \
    python3 \
    python3-pip \
    libtool \
    autoconf \
    g++ \
    pkg-config \
    libreadline-dev \
    sudo \
    vim \
    wget

# === Clone and build OpenThread ===
WORKDIR /app
RUN git clone https://github.com/openthread/openthread.git
WORKDIR /app/openthread

# Bootstrap build system
RUN ./script/bootstrap

# Build POSIX CLI FTD
# Build POSIX CLI FTD
RUN ./script/cmake-build posix
RUN ./script/cmake-build simulation

# Copy in entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose entrypoint
ENTRYPOINT ["/entrypoint.sh"]
