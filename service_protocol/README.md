# Service Protocol & Store-and-Forward Layer

Implements Layer 3 of the MeshAid architecture. Provides compact binary message packing, HMAC-SHA256 authentication, replay protection, rate limiting, and persistent priority queueing for the LoRa mesh network.

## Files

- `schema.py`: Message types, binary packing/unpacking, and HMAC signing.
- `replay_guard.py`: Sliding window replay protection.
- `rate_limiter.py`: Token bucket rate limiting.
- `gateway.py`: Gateway verification pipeline.
- `store_and_forward.py`: Persistent priority queue.
- `counter.py`: Monotonic sequence counter persistence.
- `radio_interface.py`: Meshtastic radio wrapper.
- `queue_drainer.py`: Background queue worker.
- `test_protocol.py`: Unit tests.
- `provision_keys.py`: Cryptographic key generation.

## Dependencies

- `meshtastic>=2.3.0`

## Message Types

- **CHECKIN**: Safety status, name, group size.
- **RESOURCE_REQUEST**: Resource type, quantity, urgency, notes.
- **MEDICAL_URGENT**: Severity, condition code, patient name, age.
- **ACK**: Reserved for future acknowledgments.

## Security Properties

- **Authentication**: Per-Help-Point HMAC-SHA256 (8-byte truncated).
- **Integrity**: Entire header and payload covered by MAC.
- **Replay Protection**: Sliding window of 32 sequence numbers.
- **Rate Limiting**: 20 messages per 5 minutes per node.
- **Encryption**: None. Messages are authenticated but not encrypted per ADS scope.

## Testing and Provisioning

Run unit tests:
python3 test_protocol.py

Generate development keys:
python3 provision_keys.py <number_of_help_points>
