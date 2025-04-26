# Docker 

- Use a Single ZephyrOS Image: You can pull the ZephyrOS image once and reuse it across all containers
  - each container :  ZephyrOS image & emulation for the specific device 
- Image mayne  build a custom ZephyrOS image with OpenThread
-  Custom Bridge Network for IPv6 Communication
- Multi-Container Setup with Docker Compose
  - NODE_ROLE Environment Variable
  -  Resource Allocation for Docker Containers
5. Docker Volumes for Persistent Data

## Tested /Devices

* Nordic nRF52840

| Type | Architecture        | Role                 |
|------|---------------------|----------------------|
| FTD  | Nordic (nRF52840)   | Border Router  & RCP |
|      |                     |                      |
| FTD  | Nordic (nRF52840)   | FED                  |
|      |                     | REED                 |
|      |                     | Router               |


* promotions
- FED → REED: ( cannot promote  unless it was initially a REED).
- REED → Router: (A REED can promote to Router if the network requires a new Router).
* demotions
*  REED → FED: (A REED can be demoted to FED if it no longer qualifies to be promoted to Router
*  Router → FED: (A Router can be demoted to FED if it loses routing capabilities or becomes unnecessary).


## Docker network 
* each container will : 
-  custom bridge network  : , assign IPs to each container, and allow them to communicate with each other within the OpenThread simulation.

### 1. Create a Custom Docker Bridge Network with IPv6
 - to configure Docker to enable IPv6 by editing the /etc/docker/daemon.json
```json
 {
   "ipv6": true,
   "fixed-cidr-v6": "fd00:abcd:1234::/64"
   }
``` 
Restart Docker to apply these settings:
`sudo systemctl restart docker
`
###  2 Docker Compose to create a custom bridge network
#### Dynamically 
- let Docker handle the dynamic assignment of IPv6 addresses.
	
	```ymal
	
	version: '3.7'
	
	services:
	  node1:
	    image: zephyros_image
	    networks:
	      openthread_network: {}
	......
	
	networks:
	  openthread_network:
	    driver: bridge
	    ipam:
	      driver: default
	      config:
	        - subnet: "fd00:abcd:1234::/64"  # Define the IPv6 subnet
	```

#### Static 
-  static IP addressing and careful network planning are generally preferred
	```ymal
	version: '3.7'
	
	services:
	  node1:
	    image: zephyros_image
	    networks:
	      openthread_network:
	        ipv6_address: "fd00:abcd:1234::2"  # Static address for node 1

	.... 	
	networks:
	  openthread_network:
	    driver: bridge
	    ipam:
	      driver: default
	      config:
	        - subnet: "fd00:abcd:1234::/64"  # IPv6 subnet for the custom network
	
	```

- start
  - `docker-compose up`
- Verify the Dynamic IPv6 Addresses:
  - ` docker inspect <container_name_or_id> | grep "IPAddress" `



---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



- If you want to emulate the devices accurately in a real-life setup, you should allocate the correct resources (CPU, memory) in your Docker containers to reflect the actual resource constraints of each device architecture (e.g., nRF52840, CC2652, EFR32MG21), even when using Renode for emulation.

##  Mine  
Create the Base Docker Image for Renode with ZephyrOS and OpenThread
- By configuring the entrypoint in Docker Compose, you can ensure that each container runs the correct emulation for its respective device architecture and role.

- volumes: We mount the renode-scripts directory into the container to provide the appropriate Renode scripts for each device.
- entrypoint: This is where we specify the Renode script for each device. For example, the fed_1 device uses the script nordic_nrf52840.resc, and the border_router uses nordic_nrf52840_border_router.resc.


format :
	Role:  FTD
	HW: nordic, texas,silicon
	type : BR, FED, REED

* Renode
```Docker
 renode-scripts/
    BR_nordic_FTD.resc
    FED_nordic_FTD.resc
    REED_nordic_FTD.resc
    FED_texas_FTD.resc
    REED_texas_FTD.resc
    FED_silicon_FTD.resc
    REED_silicon_FTD.resc
```

* docker-compose.yml:
```Docker
 image: 
    networks:
      openthread_network:
        ipv6_address:
    environment:
      - DEVICE_ROLE=
      - ARCHITECTURE=
    volumes:
      - ./renode-scripts:/renode-scripts
    entrypoint: ["renode", "/renode-scripts/.resc"]
    mem_limit:
    cpus: 
```


---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# - dynamically add more devices    
	- Since Docker Compose is used for defining and running multi-container Docker applications, you have the option to scale services or add new services at runtime.
## 1. Using Docker Compose to Dynamically Add Devices:
A. Scale an Existing Service `docker-compose up --scale FED_nordic_FTD=5`
C. Use `docker-compose.override.yml` for Runtime Flexibility:

## 2. Dynamic Configuration without Restarting Containers (Advanced):
 - Network/renode Reconfiguration: You can add a new container to the existing networ

## 3. Automated Device Addition Using Scripts:
 - Modifies docker-compose.yml or docker-compose.override.yml based on input
- Runs docker-compose up to bring the new devices online.


# requirements 
## Step 1: Baseline Measurements
Deploy an initial network with a fixed number of devices
Stabilize the networ
Profile performance:
## Step 2: Topology Scaling
Adding/Removing  Devices:
- ✔ Use docker-compose.override.yml for controlled scaling.
- Using docker-compose scale (but it works only for identical nodes):

## Step 3: Role Changes
Leader Re-election:
Router to End Device Transition (Demotion):
End Device to Router Transition (Promotion)

---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Step 2 Docker : Topology Scaling

## Example Bash Script for Adding a New Device:

```bash
#!/bin/bash

# Define new device parameters
NEW_DEVICE_NAME="FED_texas_FTD_2"
NEW_DEVICE_IP="fd00:abcd:1234::9"
ARCHITECTURE="CC2652"

# Add a new service to docker-compose.override.yml (or directly to docker-compose.yml)
echo "
  $NEW_DEVICE_NAME:
    image: renode_zephyros_image
    networks:
      openthread_network:
        ipv6_address: \"$NEW_DEVICE_IP\"
    environment:
      - DEVICE_ROLE=fed
      - ARCHITECTURE=$ARCHITECTURE
    volumes:
      - ./renode-scripts:/renode-scripts
    entrypoint: [\"renode\", \"/renode-scripts/FED_texas_FTD.resc\"]
    mem_limit: 256m
    cpus: 0.5
" >> docker-compose.override.yml

# Bring up the new device
docker-compose up -d

```

# Example Bash Script to Remove a Device:

```bash
#!/bin/bash

# Define the name of the container you want to remove
DEVICE_NAME="FED_texas_FTD_2"  # Adjust to the device name you want to remove
DEVICE_IP="fd00:abcd:1234::9"

# Stop the container for the device
docker stop $DEVICE_NAME

# Remove the container
docker rm $DEVICE_NAME

# Optionally, remove the device's entry from docker-compose.override.yml
# Find and remove the block corresponding to this device
sed -i "/$DEVICE_NAME:/,/^\s*$/d" docker-compose.override.yml

# Rebuild and restart the services (without the removed device)
docker-compose up -d

```

 - If you want to remove a device dynamically without manually modifying the docker-compose.yml file, you can simply stop and remove the container, and Docker will handle the network reconfiguration as long as the service definitions are still in the docker-compose.yml

```bash
#!/bin/bash

# Define the container name of the device you want to remove
DEVICE_NAME="FED_texas_FTD_2"  # Replace with the actual device container name

# Stop the container for the device
docker stop $DEVICE_NAME

# Remove the container
docker rm $DEVICE_NAME

# Rebuild the services without the removed container
docker-compose up -d
```

## Step 3 Docker : Role Changes
- After the first run, you don't need to modify the Docker files to force promotion or demotion.
-  OpenThread provides mechanisms to influence role promotion and demotion:

## # Function: Controls whether a device is eligible to become a router.
- otThreadSetRouterEligible()

## # Function: Suggests a specific Router ID when promoting.
- otThreadSetPreferredRouterId()

## # Function: Forces a Router to become a REED (Router Eligible End Device).
- otThreadReleaseRouterId()

## # Function: Forces a node to promote to a Router.
- otThreadBecomeRouter()

## # Function: Forces a device to become the Leader.
- otThreadBecomeLeader()

-------------------------------------------------------------------------------------------------------------\
2️⃣ Generate a Device List for Selection

Since each device has a structured definition, you can store them in a YAML or JSON file for automation.

```yaml
devices:
- name: "border_router_nordic"
  architecture: "nRF52840"
  role: "Border Router"
  ipv6: "fd00:abcd:1234::2"

- name: "fed_nordic"
  architecture: "nRF52840"
  role: "FED"
  ipv6: "fd00:abcd:1234::3"
  ..... 

```
```python
import yaml

# Load device list
with open("devices.yml", "r") as f:
    devices = yaml.safe_load(f)["devices"]

# Define selection criteria (modify as needed)
ARCHITECTURE_FILTER = ["nRF52840", "CC2652"]  # Example: Only select Nordic & Texas
ROLE_FILTER = ["Router", "REED"]  # Example: Only add Routers & REEDs

# Filter devices based on criteria
selected_devices = [
    d for d in devices if d["architecture"] in ARCHITECTURE_FILTER and d["role"] in ROLE_FILTER
]

# Generate override file content
override_content = {"version": "3.7", "services": {}}

for device in selected_devices:
    override_content["services"][device["name"]] = {
        "image": "renode_zephyros_image",
        "networks": {
            "openthread_network": {"ipv6_address": device["ipv6"]}
        },
        "environment": [
            f"DEVICE_ROLE={device['role']}",
            f"ARCHITECTURE={device['architecture']}"
        ],
        "volumes": ["./renode-scripts:/renode-scripts"],
        "entrypoint": ["renode", f"/renode-scripts/{device['role']}_{device['architecture']}.resc"],
        "mem_limit": "256m",
        "cpus": "0.5"
    }

# Save the override file
with open("docker-compose.override.yml", "w") as f:
    yaml.dump(override_content, f, default_flow_style=False)

print("Updated docker-compose.override.yml with selected devices.")
```