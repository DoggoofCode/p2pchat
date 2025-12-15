import queue
import threading

from p2pchat.packet.packet_communicator import PacketGateway


def test_incoming():
    # Setup the responder
    shut_down = threading.Event()
    output: queue.Queue[bytes] = queue.Queue()
    comm = PacketGateway(shut_down, host="192.168.1.23")
    responder = threading.Thread(target=incoming, args=(comm, shut_down, output))
    responder.start()

    # Send bytes
    comm.send(b"Test123\xff", target_address=("192.168.1.23", 6767))
    prog_output = output.get(timeout=1)

    print(prog_output)
    # Shut down
    shut_down.set()
    comm.receiver_thread.join()
    responder.join()
    comm.close_socks()


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
    test_incoming()


if __name__ == "__main__":
    main()
