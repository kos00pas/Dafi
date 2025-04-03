# Use a base Zephyr build environment image
FROM zephyrprojectrtos/zephyr-build:latest
USER root

# Install dependencies for Renode and other necessary tools
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    python3-pip \
    build-essential \
    python3-setuptools \
    git \
    libusb-1.0-0-dev \
    libtool \
    automake \
    pkg-config \
    unzip

# Download and extract Renode (GitHub latest)
RUN curl -L -o renode.tar.gz https://github.com/antmicro/renode/releases/download/v1.13.0/renode-1.13.0.linux-portable.tar.gz && \
    tar xzf renode.tar.gz -C /usr/local/ && \
    rm renode.tar.gz

# Add Renode to the PATH
ENV PATH="/usr/local/renode:${PATH}"

# Set the working directory to the location where the repo will be cloned
WORKDIR /workspace

# Clone the repository
RUN git clone https://github.com/antmicro/renode-zephyr-nrf52840.git

# Set the working directory to the cloned repository
WORKDIR /workspace/renode-zephyr-nrf52840

# Run the prepare_zephyr.sh script to install Zephyr dependencies
RUN ./prepare_zephyr.sh

# Build the Zephyr binaries (this is the part where we build the Zephyr project)
RUN ./build_binaries.sh

# Expose any required ports (optional, depends on your configuration)
EXPOSE 8000

# Set the default command to run Renode with a Zephyr nRF52840 simulation
CMD ["renode", "-e", "s @nrf52840.resc"]
