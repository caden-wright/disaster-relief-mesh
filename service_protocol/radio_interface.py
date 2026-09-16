import time
import threading
from meshtastic.serial_interface import SerialInterface

class RadioInterface:
    def __init__(self, port="/dev/ttyUSB0", on_receive_callback=None):
        self.port = port
        self.interface = None
        self.on_receive_callback = on_receive_callback
        self._connect()

    def _connect(self):
        self.interface = SerialInterface(self.port)
        if self.on_receive_callback:
            self.interface.onReceive = self._handle_receive

    def _handle_receive(self, packet, interface):
        if "decoded" in packet and "payload" in packet["decoded"]:
            payload_bytes = packet["decoded"]["payload"]
            self.on_receive_callback(payload_bytes)

    def send(self, wire_bytes: bytes):
        if self.interface:
            self.interface.sendData(wire_bytes)

    def is_connected(self) -> bool:
        return self.interface is not None and self.interface.isConnected

    def close(self):
        if self.interface:
            self.interface.close()
