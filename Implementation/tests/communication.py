import random
import string



from random import choices
from string import ascii_letters, digits

def initiate_coap_announcement(ns):
    print("\n📡 Initiating CoAP message exchange...")

    receiver_id = list(ns.nodes().keys())[0]
    ns.node_cmd(receiver_id, "coap start")
    ns.node_cmd(receiver_id, "coap resource logs")
    receiver_ip = get_rloc_address(ns, receiver_id)
    print(f"🧭 Receiver Node {receiver_id} IP: {receiver_ip}")

    for node_id in ns.nodes():
        try:
            ns.node_cmd(node_id, "coap start")
            if node_id == receiver_id:
                continue

            # 🔥 Generate a random 128-char payload
            payload = ''.join(choices(ascii_letters + digits, k=128))
            cmd = f"coap post {receiver_ip} logs con {payload}"
            ns.node_cmd(node_id, cmd)

            print(f"📨 Node {node_id} sent payload: {payload[:30]}...")

        except Exception as e:
            print(f"❌ Node {node_id} failed to send message: {e}")




def get_rloc_address(ns, node_id):
    try:
        ip_list = ns.node_cmd(node_id, "ipaddr")
        for ip in ip_list:
            if ip.lower().startswith("fd") and ":0:ff:fe00:" in ip:
                return ip.strip()
    except Exception:
        pass
    return None
