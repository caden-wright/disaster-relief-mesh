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
