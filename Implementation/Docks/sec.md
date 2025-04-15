## OpenThread for CPS/IIoT Security Monitoring

### Role of OpenThread

- Used only to gather and forward security data to the cloud at fixed intervals  
- Acts as a backup security layer for remote infrastructure safety  
- Low-power, secure, and mesh-based → ideal for long-life CPS deployments  
- Operates independently of core PLC/process logic  
- Can store logs offline and sync when cloud is reachable  

---

###  Security Contributions in CPS/IIoT

- Detects physical tampering before a cyber attack  
- Mesh isolation provides local containment and zoning  
- Monitors status of neighboring devices → supports anomaly detection  
- Enables early-warning signals using lightweight alerts  
- Supports forensic investigation through historical data  

---

### Security Telemetry Types

#### Event Logs

- Denied access attempts  
- Access records (PACS logs)  
- Firmware changes or upgrades  
- Device reboots  
- Tamper events (e.g., vibration, cabinet open)  
- Unexpected neighbor table reports  

#### Alerts (Triggered Only)

- Physical Access Control Systems (PACS)  
- Safety Instrumented Systems (SIS)  
- Abnormal behavior in asset trackers  

#### Network Snapshots

- Routing paths  
- Neighbor device changes  
- Topology structure changes  

#### Device Health Monitoring

- Status reports of connected ICS/CPS components  
- Power issues, downtime, connectivity failures  

#### Use Case Example

- Remote Substation Automation  
  OpenThread nodes act as watchdogs, reporting local anomalies to the cloud while the main control system operates independently.

---

###  Benefits

- Realistic and scalable for CPS 4.0 & IIoT  
- Doesn’t interrupt or interfere with primary systems  
- Provides early warning and post-incident evidence  
- Works well in both connected and disconnected edge environments  


Security event logs
-  denied access / access record ,
- firmware changes, Tamper events, firmware changes, or unexpected neighbor reports
- reboots.
- alerts only  PACS, SIS(enviroment  monitoring )  , asset trackers
- network snapshots logging 
- devices status of other devices 
- remote substation  automation 
