import hmac
import hashlib
import struct
import time
from enum import IntEnum


class MsgType(IntEnum):
    CHECKIN = 1
    RESOURCE_REQUEST = 2
    MEDICAL_URGENT = 3
    ACK = 4


SIZE = {"u8": ("B", 1), "u16": ("H", 2), "u32": ("I", 4)}

MESSAGE_FIELDS = {
    MsgType.CHECKIN: [
        ("status", "u8"), ("name", "str20"), ("group_size", "u8"),
    ],
    MsgType.RESOURCE_REQUEST: [
        ("resource_type", "u8"), ("quantity", "u16"),
        ("urgency", "u8"), ("notes", "str20"),
    ],
    MsgType.MEDICAL_URGENT: [
        ("severity", "u8"), ("condition_code", "u8"),
        ("patient_name", "str20"), ("patient_age", "u8"),
    ],
    MsgType.ACK: [
        ("orig_seq", "u32"), ("status", "u8"),
    ],
}

HEADER_FMT = "!BBBII"
HEADER_LEN = struct.calcsize(HEADER_FMT)
MAC_LEN = 8
BYTE_CEILING = 220
SCHEMA_VERSION = 1


def _fmt_for(fields):
    parts = []
    for _, kind in fields:
        parts.append(kind[3:] + "s" if kind.startswith("str") else SIZE[kind][0])
    return "!" + "".join(parts)


def pack_payload(msg_type, values: dict) -> bytes:
    fields = MESSAGE_FIELDS[msg_type]
    args = []
    for name, kind in fields:
        v = values[name]
        if kind.startswith("str"):
            n = int(kind[3:])
            v = v.encode("ascii", "ignore")[:n].ljust(n, b"\x00")
        args.append(v)
    return struct.pack(_fmt_for(fields), *args)


def unpack_payload(msg_type, raw: bytes) -> dict:
    fields = MESSAGE_FIELDS[msg_type]
    values = struct.unpack(_fmt_for(fields), raw)
    result = {}
    for (name, kind), v in zip(fields, values):
        if kind.startswith("str"):
            v = v.split(b"\x00", 1)[0].decode("ascii", "ignore")
        result[name] = v
    return result


def _mac(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()[:MAC_LEN]


def peek_help_point_id(wire: bytes) -> int:
    return struct.unpack_from("!BBB", wire, 0)[2]


def encode_message(msg_type, seq: int, help_point_id: int, values: dict, key: bytes, timestamp=None) -> bytes:
    timestamp = timestamp or int(time.time())
    header = struct.pack(HEADER_FMT, SCHEMA_VERSION, int(msg_type), help_point_id, seq, timestamp)
    body = header + pack_payload(msg_type, values)
    wire = body + _mac(key, body)
    if len(wire) > BYTE_CEILING:
        raise ValueError(f"{len(wire)} bytes exceeds {BYTE_CEILING}-byte ceiling")
    return wire


def decode_message(wire: bytes, key: bytes) -> dict:
    body, mac = wire[:-MAC_LEN], wire[-MAC_LEN:]
    authentic = hmac.compare_digest(mac, _mac(key, body))
    version, msg_type, help_point_id, seq, timestamp = struct.unpack(HEADER_FMT, body[:HEADER_LEN])
    fields = unpack_payload(MsgType(msg_type), body[HEADER_LEN:])
    return {
        "version": version, "msg_type": MsgType(msg_type),
        "help_point_id": help_point_id, "seq": seq,
        "timestamp": timestamp, "fields": fields, "authentic": authentic,
    }
