

# === Device Role Logic ===
def add_fed(ns, x, y, exe):
    node = ns.add("router", x=x, y=y, executable=exe)
    ns.set_router_upgrade_threshold(node, 99)
    ns.set_router_downgrade_threshold(node, 1)
    ns.node_cmd(node, "mode rn")

    return node


def add_reed(ns, x, y, exe):
    node = ns.add("router", x=x, y=y, executable=exe)
    ns.node_cmd(node, "mode rdn")

    return node


def add_router(ns, x, y, exe):
    node = ns.add("router", x=x, y=y, executable=exe)
    ns.node_cmd(node, "mode rdn")
    ns.node_cmd(node, "routerselectionjitter 1")

    return node

