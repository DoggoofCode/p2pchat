import hashlib, socket, threading
from queue import Queue
from packetstruct import ReceivedInformation, ReceivedChunk

CHUNK_SIZE = 14 * 1024
PACKET_LIMIT = 16 * 1024
PORT = 6767
ADDRESS = ('127.0.0.1', PORT)

class PacketGateway:
    def __init__(self, shutdown_callback, *, host='127.0.0.1', port=6767, ):
        self.address = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.address)
        self.sock.settimeout(0.5)
        self.shutdown_callback = shutdown_callback

        self.reassembled_messages: Queue[bytes] = Queue()
        self.partial_messages: dict[bytes, ReceivedInformation] = {}  # {message_id: {chunk_num: data}}

        self.receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receiver_thread.start()

        self.sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _receive_loop(self):
        while not self.shutdown_callback.is_set():
            try:
                data, _ = self.sock.recvfrom(PACKET_LIMIT)
                chunk = ReceivedChunk.deserialize(data)
                msg_hash = chunk.message_hash

                if not self.partial_messages.get(msg_hash):
                    self.partial_messages[msg_hash] = ReceivedInformation(chunk.total_chunks, msg_hash)
                self.partial_messages[msg_hash].add_chunk(chunk)

                for hash, message in self.partial_messages.copy().items():
                    if message.complete_data:
                        self.reassembled_messages.put(message.msg_data)
                        del self.partial_messages[hash]
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[Gateway] Receiver error: {e}")

    def send(self, data: bytes, target_address=('127.0.0.1', PORT)):
        data_hash = hashlib.sha256(data).digest() # 32 byte hash

        total_chunks = (len(data) + CHUNK_SIZE - 1) // CHUNK_SIZE
        for chunk_number in range(total_chunks):
            start = chunk_number * CHUNK_SIZE
            end = start + CHUNK_SIZE
            chunk_data = data[start:end]

            chunk = ReceivedChunk(data_hash, chunk_number, total_chunks, chunk_data)
            serialized = chunk.serialize()

            if len(serialized) > PACKET_LIMIT:
                raise ValueError("Serialized packet exceeds 16 KiB limit")

            if not self.shutdown_callback.is_set():
                self.sender_sock.sendto(serialized, target_address)

    def stop(self):
        self.sock.close()
        self.sender_sock.close()
