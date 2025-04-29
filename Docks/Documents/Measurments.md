
# 1- Leader Election Phase
```text     
      ✅ step 1. Attach Status Check
            All nodes are non-detached and non-disabled — Leader Election
        
      ✅ step 2. Single Leader Verification
            One and only one node is in the `leader` state — Leader Election
        
      ✅ step 3. Valid Roles Across Nodes
            All other nodes are in `router` or `child` roles — Leader Election
        
      ✅ step 4. RLOC16 Stability
            RLOC16 does not change — leader, router (optional for child) — Leader Election 
        
      ✅ step 5. IPv6 Address Stability
            IPv6 address list (ipaddr) remains unchanged — leader, router, child — Leader Election 
        
      ✅ step 6. State Stability
            Stay in the same state across all nodes — leader, router, child — Leader Election 
        
      ✅ step 7. Routing Message Silence
            No recent routing messages (DIO/DAO) — leader, router — Leader Election 
```



#  4- Topology Convergence  = Leader election + the following
```text 
    - Proper topology convergence cannot occur without a successful leader election. 
    - (need 1-7)
    🟣 step 8. Neighbor Table Stability
           Neighbor table remains identical — leader, router (optional for child) — Topology Convergence
    
    🟣 step 9. Router Table Stability
           Router table entries and routes do not change — leader, router — Topology Convergence
    
    🟣 step 10. Prefix & Route Propagation
           Prefixes and routes remain stable — leader, router — Topology Convergence
    
    🟣 step 11. End-to-End Reachability
            All mesh-local addresses are mutually reachable (ping) — leader, router, child — Topology Convergence
```


# 2- RPL Route Stability & Update Efficiency
```text 
	📖 Step 12: Route Table Snapshot Stability( need 4,5,6 )
		     • After convergence, capture route tables from all nodes at regular intervals (e.g. every 10s for 1–2 minutes), and compare them to ensure that routing paths remain consistent and predictable, with stable next-hop and destination entries.
	📖 Step 13: DIO/DAO Message Decay Time( need 12)
		     • Measure the time from convergence until the last DIO or DAO message is seen in the logs. This reveals how quickly the network suppresses routing updates, indicating Trickle algorithm efficiency and protocol quietness
```


# 5- Multicast Propagation Delay (MPD)
```text 
	📍 Step 14: Multicast Trigger( need 1-13)
			  § Initiate a multicast DIO or DAO message from a selected node and log the exact send timestamp. This marks the start of propagation measurement.

	📍 Step 15: Reception Logging( need 14)
			  § Capture the timestamp when each node receives the multicast message for the first time, allowing per-node delay tracking.

	📍 Step 16: Compute MPD( need 15)
              § Calculate the propagation delay per node (receive_time - send_time) and report the maximum value as the Multicast Propagation Delay (MPD), representing the time required for the message to reach all nodes.
```
L -> R
L -> C
R -> R
R -> C
R -> L
C -> R
C -> L

# 3&6- Packet Delivery & Communication & IPv6 Packet Forwarding Efficiency  
```text  
     🍞 Step 17  (need 1-11) 
                § Identify multiple pairs of nodes in your OTNS environment for testing.
                    □ 30% of the network 
                    □ A: L-R: all 
                    □ B: L-C : all 
                    □ R-R  : 3 (30 -A-B )/4
                    □ R-C:  (30 -A-B )/4	
                §  Send CoAP echo requests from a source to destination node multiple times
                § Collect logs to verify packet delivery results.
                § Parse logs, count packets sent vs. packets received.
                § Calculate Packet Delivery Ratio (PDR) and Packet Loss Rate (PLR)
                § For each source–destination pair from Step 17:
                    • Forwarding Success Rate = (Packets Received / Packets Sent) × 100%
                    • Record the number of hops for each delivered packet using OTNS trace logs or CLI (`route`, `neighbor`).
                    • Calculate Total Transmissions:
                        □ Total transmissions = Sum of all hop-level transmissions across all packets.
                        □ (Example: a 3-hop delivery = 3 transmissions)
                    • Calculate IPv6 Packet Forwarding Efficiency:
                        □ Efficiency (%) = (Packets Received / Total Transmissions) × 100%

```



# 7- 6LoWPAN Compression Efficiency,
```text 
    🚞 Step 19 (needs Steps 1–11)
        This step reuses the CoAP traffic and delivery traces generated during Step 17.  
        It extends the analysis by inspecting packet size and 6LoWPAN header compression using PCAP captures to assess protocol efficiency on constrained links.
            1. Capture 6LoWPAN Packet Sizes
                   - Use OTNS with packet logging (capturing to `current.pcap`, then copying it as `lowpan.pcap`).
                   - After Step 17 CoAP communication, copy `current.pcap` ➔ `lowpan.pcap`.
                   - For each packet inside `lowpan.pcap`:
                       - Check if it is a UDP packet with destination port 5683 (manual CoAP detection).
                       - If yes, extract:
                         - Frame size (full IEEE 802.15.4 packet size)
                         - Compressed IPv6/UDP header size (from 6LoWPAN layer)
                         - Payload length (from UDP layer)
                
            2. Compare Raw vs. Compressed Headers
                   - Reference uncompressed size is `IPv6 (40 bytes) + UDP (8 bytes) = 48 bytes`.
                   - Compute Compression Ratio:
                         ```
                         Compression Ratio = Compressed Header Size / 48
                         ```
                   - Additionally, inspect:
                     - CID (Context ID) usage (if visible from 6LoWPAN fields)
                     - Address elision (e.g., if link-local addresses are compressed)
                     - Port compression (e.g., if ports are elided or compressed)

            3. Analyze Compression Behavior by Topology
                   - Use the same node pairs generated in Step 17 (e.g., L➔R, L➔C, R➔R, R➔C).
                   - Group the compression results according to role-pairs:
                     - Leader → Router
                     - Leader → Child
                     - Router → Router
                     - Router → Child
                   - Compare:
                     - Average compressed header size per role pair.
                     - Compression ratio consistency across pairs.
                     - Impact of routing hop count (if known) on compression efficiency.
```

