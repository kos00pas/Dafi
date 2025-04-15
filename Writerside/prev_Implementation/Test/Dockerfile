# Use Ubuntu as base image
FROM ubuntu:22.04

# ==cd
WORKDIR /opt/zephyrproject

# Install Python and dependencies
RUN apt update
RUN apt install -y   git
RUN apt install -y cmake
RUN apt install -y     ninja-build
RUN apt install -y     gperf
RUN apt install -y     ccache
RUN apt install -y     dfu-util
RUN apt install -y     device-tree-compiler
RUN apt install -y     wget
RUN apt install -y     python3-dev
RUN apt install -y     python3-pip
RUN apt install -y     python3-setuptools
RUN apt install -y     python3-wheel
RUN apt install -y     python3-venv
RUN apt install -y     xz-utils
RUN apt install -y     file
RUN apt install -y     make
RUN apt install -y     gcc
RUN apt install -y     gcc-multilib
RUN apt install -y     g++-multilib
RUN apt install -y     libsdl2-dev
RUN apt install -y     libmagic1
RUN DEBIAN_FRONTEND=noninteractive apt install -y python3-tk

# Create virtual environment and install west
RUN python3 -m venv .venv && \
    . .venv/bin/activate && \
    pip install --upgrade pip && \
    pip install west

# Initialize west (Zephyr setup)
RUN . .venv/bin/activate && \
    west init -l zephyr || west init && \
    west update && \
    west zephyr-export && \
    west packages pip --install

COPY mandatory-files /opt/zephyrproject/mandatory-files/

ENTRYPOINT ["/bin/bash", "-c", \
  ". /opt/zephyrproject/.venv/bin/activate && \
   python mandatory-files/helper_script.py && \
   python mandatory-files/app.py && \
   bash mandatory-files/your_script.sh"]

