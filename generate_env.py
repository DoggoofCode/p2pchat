import logging
import queue
import threading
import time

from p2pchat.packet.packet_communicator import PacketGateway
from p2pchat.response.responder import Responder

logging.basicConfig(filename="user_data/main.log", filemode="w")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def main():
    # Shutdown event
    shutdown = threading.Event()

    # Create a response queue
    output: queue.Queue[bytes] = queue.Queue()
    comm = PacketGateway(shutdown)
    responder = Responder(shutdown, output, comm)

    # Create a receiver thread
    receiver_thread = threading.Thread(target=incoming, args=(comm, shutdown, output))
    receiver_thread.start()

    time.sleep(1)
    logger.debug("Complete, waiting for threads to finish...")
    shutdown.set()
    logger.debug("Shutdown set")
    comm.receiver_thread.join()
    logger.debug("Comm Thread joint")
    responder.responder_thread.join()
    logger.debug("Responder Thread joint")
    receiver_thread.join()
    logger.debug("Receiver Thread joint")
    comm.close_socks()
    logger.debug("Comm Sockets closed")
    logger.debug("Point precision!")


def incoming(
    communicator: PacketGateway, shutdown: threading.Event, output: queue.Queue[bytes]
):
    while not shutdown.is_set():
        try:
            msg = communicator.reassembled_messages.get(timeout=0.5)
            output.put(msg)
        except queue.Empty:
            continue


if __name__ == "__main__":
    main()
