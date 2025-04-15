def initiate_coap_announcement(ns):
    print("\n📡 Initiating CoAP message exchange...")

    receiver_id = list(ns.nodes().keys())[0]
    ns.node_cmd(receiver_id, "coap start")
    ns.node_cmd(receiver_id, "coap resource logs")  # Correct: register resource
    receiver_ip = get_rloc_address(ns, receiver_id)
    print(f"🧭 Receiver Node {receiver_id} IP: {receiver_ip}")

    for node_id in ns.nodes():
        try:
            ns.node_cmd(node_id, "coap start")
            if node_id == receiver_id:
                continue

            cmd = f"coap post {receiver_ip} logs con hello"
            ns.node_cmd(node_id, cmd)
            print(f"✅ Node {node_id} sent 'hello' to Node {receiver_id}")

        except Exception as e:
            print(f"❌ Node {node_id} failed to send 'hello': {e}")





def get_rloc_address(ns, node_id):
    try:
        ip_list = ns.node_cmd(node_id, "ipaddr")
        for ip in ip_list:
            if ip.lower().startswith("fd") and ":0:ff:fe00:" in ip:
                return ip.strip()
    except Exception:
        pass
    return None
