import threading
import time

class QueueDrainer(threading.Thread):
    def __init__(self, queue, radio_interface, check_interval=5.0):
        super().__init__(daemon=True)
        self.queue = queue
        self.radio_interface = radio_interface
        self.check_interval = check_interval
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            if self.radio_interface.is_connected():
                pending = self.queue.get_pending()
                if pending:
                    wire = pending[0]
                    self.radio_interface.send(wire)
                    self.queue.acknowledge(wire)
            time.sleep(self.check_interval)

    def stop(self):
        self.running = False
