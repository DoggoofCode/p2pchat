import argparse
import asyncio
import logging
import queue
import threading

from p2pchat.packet.packet_communicator import PacketGateway
from p2pchat.response.responder import Responder

logging.basicConfig(filename="user_data/main.log", filemode="w")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


async def main():
    # Verify the port of the container
    parser = argparse.ArgumentParser(
        prog="Debug environement generator",
        description="Generates and runs debug environments for p2pchat",
    )

    parser.add_argument("-p", "--port", type=int, default=6767)
    args = parser.parse_args()

    print(f"Running on port: \x1b[1m{args.port}\x1b[0m")

    # Shutdown event
    shutdown = threading.Event()

    # Create a response queue
    output: queue.Queue[bytes] = queue.Queue()
    comm = PacketGateway(shutdown, port=args.port)
    responder = Responder(shutdown, output, comm)
    # 
    # Create a receiver thread
    receiver_thread = threading.Thread(target=incoming, args=(comm, shutdown, output))
    receiver_thread.start()

    await responder.send_message_identifier()

    exit_text = ""
    exit_text = input("")
    while exit_text != "q":
        print("If you want to exit type 'q'")
        exit_text = input("")
    print("\x1b[1mKilling the program!\x1b[0m")
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
    asyncio.run(main())
