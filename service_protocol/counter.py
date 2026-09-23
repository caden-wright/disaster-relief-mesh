import os
import threading

try:
    import fcntl
except ImportError:
    fcntl = None


class SequenceCounter:
    def __init__(self, persist_path="meshaid_counter.txt"):
        self.persist_path = persist_path
        self.lock = threading.Lock()
        self._value = self._load()

    def _load(self):
        if not os.path.exists(self.persist_path):
            return 0

        try:
            with open(self.persist_path, "r") as f:
                if fcntl is not None:
                    fcntl.flock(f, fcntl.LOCK_SH)

                try:
                    value = int(f.read().strip())
                finally:
                    if fcntl is not None:
                        fcntl.flock(f, fcntl.LOCK_UN)

            return value

        except (ValueError, OSError):
            return 0

    def _save(self, value):
        temp_path = self.persist_path + ".tmp"

        with open(temp_path, "w") as f:
            if fcntl is not None:
                fcntl.flock(f, fcntl.LOCK_EX)

            try:
                f.write(str(value))
                f.flush()
                os.fsync(f.fileno())
            finally:
                if fcntl is not None:
                    fcntl.flock(f, fcntl.LOCK_UN)

        os.replace(temp_path, self.persist_path)

    def next(self):
        with self.lock:
            self._value += 1
            self._save(self._value)
            return self._value

    def current(self):
        with self.lock:
            return self._value