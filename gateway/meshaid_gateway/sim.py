"""
Traffic simulator. Builds real frames with service_protocol's encoder and pushes
them into a gateway running with `--radio sim`, through its dev API.

    python -m meshaid_gateway.sim normal --count 10
    python -m meshaid_gateway.sim demo                # continuous mixed traffic until Ctrl-C
    python -m meshaid_gateway.sim spoof               # wrong key + unprovisioned Help Point
    python -m meshaid_gateway.sim replay              # valid frame, then the same bytes again
    python -m meshaid_gateway.sim malformed
    python -m meshaid_gateway.sim stale               # authentic frame far behind the replay window
    python -m meshaid_gateway.sim burst --count 25    # trips the post-auth rate limit
    python -m meshaid_gateway.sim drop-node --node HP2 / restore-node --node HP2
"""

import argparse
import json
import os
import random
import time
import urllib.request

from .config import GATEWAY_DIR, Config
from .protocol_bridge import MsgType, encode_message, load_key_store
from .radio import SIM_HP_NODE, SIM_NODES

STATE_PATH = GATEWAY_DIR / ".sim_state.json"
ATTACKER_NODE = 0x0BADBEEF
NODE_ALIASES = {short: num for num, (_, _, short, _) in SIM_NODES.items()}


class Sim:
    def __init__(self, url: str, key_store_path):
        self.url = url.rstrip("/")
        self.keys = load_key_store(key_store_path)
        self.state = json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {}

    # --- plumbing ---------------------------------------------------------

    def _post(self, path: str, body: dict):
        req = urllib.request.Request(self.url + path, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())

    def next_seq(self, hp_id: int) -> int:
        # Start high so the "stale" scenario can go 100 behind without going negative.
        seq = self.state.get(str(hp_id), 1000) + 1
        self.state[str(hp_id)] = seq
        STATE_PATH.write_text(json.dumps(self.state))
        return seq

    def send(self, wire: bytes, hp_id=None, from_node=None, label=""):
        if from_node is None:
            from_node = SIM_HP_NODE.get(hp_id, ATTACKER_NODE)
        hops = SIM_NODES.get(from_node, (None, None, None, 1))[3]
        self._post("/api/dev/inject", {"wire_hex": wire.hex(), "from_node": from_node, "hops": hops,
                                       "snr": round(random.uniform(-5, 10), 1)})
        print(f"  sent {len(wire):3d} B  {label}")

    def frame(self, msg_type, values, hp_id=None, seq=None, key=None) -> tuple:
        hp_id = hp_id or random.choice(sorted(self.keys))
        seq = seq if seq is not None else self.next_seq(hp_id)
        wire = encode_message(msg_type, seq=seq, help_point_id=hp_id, values=values, key=key or self.keys[hp_id])
        return wire, hp_id, seq

    # --- message generators ------------------------------------------------

    @staticmethod
    def random_values():
        kind = random.choices([MsgType.CHECKIN, MsgType.RESOURCE_REQUEST, MsgType.MEDICAL_URGENT], [5, 4, 1])[0]
        if kind == MsgType.CHECKIN:
            return kind, {"status": random.choices([1, 2, 3], [8, 2, 1])[0], "name": "",
                          "group_size": random.randint(1, 6)}
        if kind == MsgType.RESOURCE_REQUEST:
            return kind, {"resource_type": random.choice([1, 2, 3, 4, 5]), "quantity": random.randint(1, 40),
                          "urgency": random.choices([1, 2, 3], [3, 5, 2])[0], "notes": ""}
        return kind, {"severity": random.choices([1, 2, 3], [3, 4, 2])[0], "condition_code": random.randint(1, 5),
                      "patient_name": "", "patient_age": random.randint(2, 90)}

    def normal(self, count=1, hp_id=None):
        for _ in range(count):
            kind, values = self.random_values()
            wire, hp, seq = self.frame(kind, values, hp_id=hp_id)
            self.send(wire, hp, label=f"{kind.name} hp={hp} seq={seq}")

    # --- scenarios --------------------------------------------------------

    def scenario_normal(self, a):
        self.normal(a.count, a.hp)

    def scenario_demo(self, a):
        print("Sending mixed traffic every 2-6 s (Ctrl-C to stop)")
        try:
            while True:
                self.normal(1, a.hp)
                time.sleep(random.uniform(2, 6))
        except KeyboardInterrupt:
            pass

    def scenario_spoof(self, a):
        hp = a.hp or 1
        wire, _, seq = self.frame(MsgType.MEDICAL_URGENT, {"severity": 3, "condition_code": 3, "patient_name": "",
                                                            "patient_age": 40}, hp_id=hp, key=os.urandom(32))
        self.send(wire, from_node=ATTACKER_NODE, label=f"SPOOF: medical claiming hp={hp}, forged key -> expect unauthentic")
        wire = encode_message(MsgType.RESOURCE_REQUEST, seq=1, help_point_id=99, key=os.urandom(32),
                              values={"resource_type": 1, "quantity": 500, "urgency": 3, "notes": ""})
        self.send(wire, from_node=ATTACKER_NODE, label="SPOOF: unprovisioned hp=99 -> expect unknown_node")

    def scenario_replay(self, a):
        hp = a.hp or 1
        wire, _, seq = self.frame(MsgType.RESOURCE_REQUEST, {"resource_type": 1, "quantity": 20, "urgency": 3,
                                                              "notes": ""}, hp_id=hp)
        self.send(wire, hp, label=f"original resource request hp={hp} seq={seq} -> expect accepted")
        time.sleep(1)
        for i in range(a.count if a.count > 1 else 2):
            self.send(wire, from_node=ATTACKER_NODE, label=f"REPLAY #{i + 1} of seq={seq} -> expect duplicate")

    def scenario_malformed(self, a):
        hp = a.hp or 1
        self.send(os.urandom(6), from_node=ATTACKER_NODE, label="6 random bytes -> expect malformed (too short)")
        good, _, _ = self.frame(MsgType.CHECKIN, {"status": 1, "name": "", "group_size": 1}, hp_id=hp)
        self.send(good[:20], hp, label="truncated check-in -> expect malformed")
        self.send(bytes([1, 9, hp]) + os.urandom(16), hp, label="unknown msg_type 9 -> expect malformed")

    def scenario_stale(self, a):
        hp = a.hp or 1
        self.normal(1, hp)
        seq = self.state[str(hp)] - 100
        wire, _, _ = self.frame(MsgType.CHECKIN, {"status": 1, "name": "", "group_size": 2}, hp_id=hp, seq=seq)
        self.send(wire, hp, label=f"authentic but seq={seq} (100 behind) -> expect flagged_stale")

    def scenario_burst(self, a):
        hp = a.hp or 1
        n = a.count if a.count > 1 else 25
        print(f"Burst of {n} check-ins from hp={hp} (limit is 20 per 5 min)")
        for _ in range(n):
            wire, _, seq = self.frame(MsgType.CHECKIN, {"status": 1, "name": "", "group_size": 1}, hp_id=hp)
            self.send(wire, hp, label=f"seq={seq}")

    def _node(self, a) -> int:
        if a.node is None:
            raise SystemExit("--node is required (e.g. HP2, R1, or a node number)")
        return NODE_ALIASES.get(a.node.upper()) or int(a.node, 0)

    def scenario_drop_node(self, a):
        n = self._node(a)
        self._post("/api/dev/node", {"node_num": n, "online": False})
        print(f"Node {n:#x} stops sending heartbeats (goes degraded/down after the configured thresholds)")

    def scenario_restore_node(self, a):
        n = self._node(a)
        self._post("/api/dev/node", {"node_num": n, "online": True})
        print(f"Node {n:#x} back online")


SCENARIOS = ["normal", "demo", "spoof", "replay", "malformed", "stale", "burst", "drop-node", "restore-node"]


def main(argv=None):
    p = argparse.ArgumentParser(prog="meshaid_gateway.sim", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scenario", choices=SCENARIOS)
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--hp", type=int, help="Help Point id to send as")
    p.add_argument("--node", help="node for drop-node/restore-node: GW, R1, R2, HP1, HP2 or a number")
    p.add_argument("--url", default="http://127.0.0.1:8000")
    p.add_argument("--keys", default=str(Config().key_store_path))
    a = p.parse_args(argv)

    sim = Sim(a.url, a.keys)
    getattr(sim, "scenario_" + a.scenario.replace("-", "_"))(a)


if __name__ == "__main__":
    main()
