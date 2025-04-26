# Project Results

## Workflow of Impact
- Project goal and impact
- Define Experiments
- Define Metrics and the order of them
- Implementation (see Workflow of Tests section below)
- (Next) Preparation of a Framework to evaluate IoT protocols in environments:
  - Simulator
  - Emulator of devices
  - Real devices
- (Next) Find the best solutions among available tools and attempt framework implementation

## Workflow of Tests
- Learn about OpenThread Architecture
- Toolchain: Ubuntu: Multiple CLI devices in the host (no Docker)
- Docker Windows Engine & WSL:
  - Single Container
  - Multiple Containers
- Ubuntu & Docker & Emulation:
  - Single Device (simulation only)
  - Multiple Devices (simulation only, emulation failed)
- WSL + OTNS (OpenThread Network Simulator)
- Attempted Renode Emulation (nRF52840 emulation attempt)
- WSL Networking Debugging for OTNS + Docker (port mapping, localhost issues)
- Thread Commissioning Tests (Commissioner/Joiner experiments)
- Multi-hop Mesh Topology Experiments (basic topology formation tests)


## Framework Baseline Decision

After analyzing all previous experiments, the most reliable and scalable configuration is:

- Use  Windows  WSL toolchain installation.
- Deploy a Single Container hosting:
  - Multiple OpenThread CLI instances (e.g., `ot-cli-ftd`) launched as parallel processes inside the container.
  - A central Python control script to manage devices (start, monitor, command).
- This setup will be used as the baseline to implement and validate the Dynamic Analysis Framework (DAfI) before moving to emulation or real devices in future work.

