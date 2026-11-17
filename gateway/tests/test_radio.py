from pubsub import pub

from meshaid_gateway.radio import PRIVATE_APP_TOPIC, MeshtasticSource, frame_from_packet


def test_frame_from_packet_extracts_hops_and_snr():
    packet = {"from": 0x1234, "rxSnr": 6.25, "hopStart": 3, "hopLimit": 1,
              "decoded": {"portnum": "PRIVATE_APP", "payload": b"\x01\x02"}}
    f = frame_from_packet(packet, received_at=1.0)
    assert (f.wire, f.from_node, f.snr, f.hops, f.received_at) == (b"\x01\x02", 0x1234, 6.25, 2, 1.0)


def test_frame_from_packet_ignores_packets_without_bytes():
    assert frame_from_packet({"decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "hi"}}) is None


def test_only_private_app_from_own_interface_is_forwarded():
    src = MeshtasticSource("tcp:localhost")
    src.interface = object()          # stand-in for a connected interface
    got = []
    src._on_frame = got.append
    pub.subscribe(src._handle_packet, PRIVATE_APP_TOPIC)
    try:
        pkt = {"from": 1, "decoded": {"portnum": "PRIVATE_APP", "payload": b"abc"}}
        pub.sendMessage(PRIVATE_APP_TOPIC, packet=pkt, interface=src.interface)
        pub.sendMessage(PRIVATE_APP_TOPIC, packet=pkt, interface=object())   # some other interface
        pub.sendMessage("meshtastic.receive.data.TEXT_MESSAGE_APP", packet=pkt, interface=src.interface)
    finally:
        pub.unsubscribe(src._handle_packet, PRIVATE_APP_TOPIC)
    assert [f.wire for f in got] == [b"abc"]


# ---- liveness from any packet (relay "Down / never" fix) -------------------

from meshaid_gateway.radio import ANY_PACKET_TOPIC, heard_from_packet  # noqa: E402

R1, R4, GW = 0xA35A4668, 0xA35A7054, 0xF6FB9388


def test_heard_from_packet_stamps_sender_with_snr_and_hops():
    pkt = {"from": R4, "rxSnr": 6.25, "hopStart": 3, "hopLimit": 3,
           "decoded": {"portnum": "TELEMETRY_APP"}}
    (u,) = heard_from_packet(pkt, received_at=100.0)
    assert (u.node_num, u.last_heard, u.snr, u.hops_away) == (R4, 100.0, 6.25, 0)
    # node_id must be filled in, or config.json labels/roles never match
    # (R1/R3/R4 showed up as bare numbers labelled "Gateway").
    assert u.node_id == "!a35a7054"


def test_heard_from_packet_credits_the_relay_by_low_byte():
    # R4's nodeinfo arrived one hop away, forwarded by R1 (relayNode 0x68 = 104).
    pkt = {"from": R4, "hopStart": 3, "hopLimit": 2, "relayNode": 104}
    updates = heard_from_packet(pkt, received_at=5.0, known_nodes=[GW, R1, R4])
    assert [(u.node_num, u.node_id, u.last_heard) for u in updates] == [
        (R4, "!a35a7054", 5.0), (R1, "!a35a4668", 5.0)]


def test_heard_from_packet_skips_ambiguous_or_direct_relay_byte():
    twin = 0x11111168                       # also ends in 0x68
    pkt = {"from": R4, "hopStart": 3, "hopLimit": 2, "relayNode": 0x68}
    assert [u.node_num for u in heard_from_packet(pkt, known_nodes=[R1, twin, R4])] == [R4]
    direct = {"from": R4, "hopStart": 3, "hopLimit": 3, "relayNode": 0x54}   # 0 hops: no relay
    assert [u.node_num for u in heard_from_packet(direct, known_nodes=[R1, R4])] == [R4]


def test_any_packet_listener_sees_subtopics_from_own_interface_only():
    class FakeInterface:
        nodesByNum = {GW: {}, R1: {}, R4: {}}

    src = MeshtasticSource("tcp:localhost")
    src.interface = FakeInterface()
    got = []
    src._on_node = got.append
    pub.subscribe(src._handle_any_packet, ANY_PACKET_TOPIC)
    try:
        pkt = {"from": R1, "rxSnr": 7.0, "decoded": {"portnum": "TELEMETRY_APP"}}
        pub.sendMessage("meshtastic.receive.telemetry", packet=pkt, interface=src.interface)
        pub.sendMessage("meshtastic.receive.telemetry", packet=pkt, interface=object())
    finally:
        pub.unsubscribe(src._handle_any_packet, ANY_PACKET_TOPIC)
    assert [u.node_num for u in got] == [R1]
