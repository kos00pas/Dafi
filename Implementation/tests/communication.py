def initiate_coap_announcement(ns):
    print("\n📡 Initiating CoAP message exchange...")

    # Choose one node (e.g., first router) as the receiver/log server
    receiver_id = list(ns.nodes().keys())[0]
    ns.node_cmd(receiver_id, "coap start")
    ns.node_cmd(receiver_id, "coap resource /logs")

    for node_id in ns.nodes():
        try:
            print(f"\n🧪 Testing `coap help` on Node {node_id}:")
            ns.node_cmd(node_id, "coap start")
            output = ns.node_cmd(node_id, "coap help")
            for line in output:
                print(f"  {line.strip()}")
        except Exception as e:
            print(f"❌ Node {node_id} failed `coap help`: {e}")


def get_rloc_address(ns, node_id):
    try:
        ip_list = ns.node_cmd(node_id, "ipaddr")
        for ip in ip_list:
            if ip.lower().startswith("fd") and ":0:ff:fe00:" in ip:
                return ip.strip()
    except Exception:
        pass
    return None
