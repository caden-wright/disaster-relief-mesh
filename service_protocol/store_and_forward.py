import json
import os
import threading
import time

class StoreAndForwardQueue:
    def __init__(self, persist_path="meshaid_queue.json", max_size=100):
        self.persist_path = persist_path
        self.max_size = max_size
        self.lock = threading.Lock()
        self.queue = []
        self._load()

    def _load(self):
        if os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, "r") as f:
                    data = json.load(f)
                    self.queue = data.get("items", [])
            except Exception:
                self.queue = []

    def _save(self):
        try:
            with open(self.persist_path, "w") as f:
                json.dump({"items": self.queue}, f)
        except Exception:
            pass

    def submit(self, wire: bytes, priority: int, mesh_available: bool) -> dict:
        with self.lock:
            entry = {
                "wire": wire.hex(),
                "priority": priority,
                "timestamp": time.time()
            }
            
            if mesh_available and len(self.queue) == 0:
                return {"status": "sent_immediately", "queue_depth": 0, "wire_to_send": wire}
            
            self.queue.append(entry)
            self.queue.sort(key=lambda x: (x["priority"], x["timestamp"]))
            
            if len(self.queue) > self.max_size:
                self.queue = self.queue[:self.max_size]
                
            self._save()
            return {"status": "queued", "queue_depth": len(self.queue), "wire_to_send": None}

    def get_pending(self) -> list:
        with self.lock:
            return [bytes.fromhex(item["wire"]) for item in self.queue]

    def acknowledge(self, wire: bytes):
        with self.lock:
            hex_wire = wire.hex()
            self.queue = [item for item in self.queue if item["wire"] != hex_wire]
            self._save()

    def clear(self):
        with self.lock:
            self.queue = []
            self._save()
