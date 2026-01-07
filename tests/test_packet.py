import queue
import threading
import unittest
from p2pchat.packet.packet_communicator import PacketGateway


class TestPacketGateway(unittest.TestCase):
    def test_incoming(self):
        # Setup the responder
        shut_down = threading.Event()
        output: queue.Queue[bytes] = queue.Queue()
        comm = PacketGateway(shut_down)
        responder = threading.Thread(target=incoming, args=(comm, shut_down, output))
        responder.start()

        # Send bytes
        comm.send(b"Test123\xff")
        prog_output = output.get(timeout=1)

        # Shut down
        shut_down.set()
        comm.receiver_thread.join()
        responder.join()
        comm.close_socks()

        self.assertTrue(shut_down.is_set(), False)
        self.assertTrue(prog_output, b"Test123\xff")


def incoming(
    communicator: PacketGateway, shut_down: threading.Event, output: queue.Queue[bytes]
):
    while not shut_down.is_set():
        try:
            msg = communicator.reassembled_messages.get(timeout=0.5)
            output.put(msg)
        except queue.Empty:
            continue


def main():
    _ = unittest.main()


if __name__ == "__main__":
    main()
