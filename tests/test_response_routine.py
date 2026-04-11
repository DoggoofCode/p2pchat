import queue
import threading
import unittest
from unittest import IsolatedAsyncioTestCase

from p2pchat.packet.packet_communicator import PacketGateway
from p2pchat.response.responder import Responder


class TestResponseRoutine(IsolatedAsyncioTestCase):
    async def test_response(self):
        # Shutdown event
        shutdown = threading.Event()

        # Create a response queue
        output: queue.Queue[bytes] = queue.Queue()
        comm = PacketGateway(shutdown)
        responder = Responder(shutdown, output, comm)

        # Create a receiver thread
        receiver_thread = threading.Thread(
            target=incoming, args=(comm, shutdown, output)
        )
        receiver_thread.start()

        response = await responder.send_message_identifier()

        shutdown.set()
        comm.receiver_thread.join()
        responder.responder_thread.join()
        receiver_thread.join()
        comm.close_socks()

        self.assertIsNotNone(response)


def incoming(
    communicator: PacketGateway, shutdown: threading.Event, output: queue.Queue[bytes]
):
    while not shutdown.is_set():
        try:
            msg = communicator.reassembled_messages.get(timeout=0.5)
            output.put(msg)
        except queue.Empty:
            continue


def main():
    _ = unittest.main()


if __name__ == "__main__":
    main()
