import queue
from packet_communicator import PacketGateway
import threading

def incoming(communicator: PacketGateway, shut_down):
    while not shut_down.is_set():
        try:
            msg = communicator.reassembled_messages.get(timeout=.5)
            print(f"Received: {msg}")
        except queue.Empty:
            continue

def shut_down_func(shut_down):
    input("")
    shut_down.set()

def main():
    print("===Testing Packet Gateway===\n\033[2mPress enter to shutdown\033[0m")
    shut_down = threading.Event()
    comm = PacketGateway(shut_down)
    responder = threading.Thread(target=incoming, args=(comm, shut_down))
    shut_down_thread = threading.Thread(target=shut_down_func, args=(shut_down,))
    shut_down_thread.start()
    responder.start()

    comm.send(b"hello there")
    comm.receiver_thread.join()
    responder.join()


    print("[Main] Shutdown complete.")


if __name__ == '__main__':
    main()
