import queue, threading, unittest
from p2pchat.packet.packet_communicator import PacketGateway

class TestPacketGateway(unittest.TestCase):
    def test_incoming(self):
        shut_down = threading.Event()
        output = queue.Queue()
        comm = PacketGateway(shut_down)
        responder = threading.Thread(target=incoming, args=(comm, shut_down, output))
        responder.start()

        comm.send(b'Test123\xFF')
        prog_output = output.get(timeout=1)

        shut_down.set()
        comm.receiver_thread.join()
        responder.join()
        comm.close_socks()

        self.assertTrue(shut_down.is_set(), False)
        self.assertTrue(prog_output, b'Test123\xFF')


def incoming(communicator: PacketGateway, shut_down, output):
    while not shut_down.is_set():
        try:
            msg = communicator.reassembled_messages.get(timeout=.5)
            output.put(msg)
        except queue.Empty:
            continue

def main():
    unittest.main()


if __name__ == '__main__':
    main()
