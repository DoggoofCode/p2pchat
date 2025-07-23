import hashlib
import socket
import threading
from queue import Queue
from .data_chunck import DataChunk

CHUNK_SIZE = 14 * 1024
PACKET_LIMIT = 16 * 1024
PORT = 6767
ADDRESS = ('127.0.0.1', PORT)

class DataInformation:
    def __init__(self, total_chunks: int, message_hash: bytes):
        self.total_chunks = total_chunks
        self.message_hash = message_hash
        self.data_list: list[DataChunk] = []

    def append(self, chunk: DataChunk):
        self.data_list.append(chunk)

    @property
    def complete_data(self) -> bool:
        return len(self.data_list) == self.total_chunks

    @property
    def msg_data(self) -> bytes:
        if not self.complete_data:
            return b''
        sorted_chunks = sorted(self.data_list, key=lambda x: x.chunk_number)
        data = list(map(lambda chunk: chunk.data, sorted_chunks))
        return b''.join(data)

class UDPCommunicator:
    def __init__(self, host='127.0.0.1', port=6767):
        self.address = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.address)

        self.reassembled_messages = Queue()
        self.partial_messages: dict[bytes, DataInformation] = {}  # {message_id: {chunk_num: data}}
        self.running = True

        self.receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receiver_thread.start()

        self.sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _receive_loop(self):
        print(f"[UDPCommunicator] Listening on {self.address}")
        while self.running:
            try:
                data, _ = self.sock.recvfrom(PACKET_LIMIT)
                chunk = DataChunk.deserialize(data)
                msg_hash = chunk.message_hash

                if not self.partial_messages.get(msg_hash):
                    self.partial_messages[msg_hash] = DataInformation(chunk.total_chunks, msg_hash)
                self.partial_messages[msg_hash].append(chunk)

                for hash, message in self.partial_messages.copy().items():
                    if message.complete_data:
                        # print("[UDPCommunicator] Message complete, adding to Queue")
                        self.reassembled_messages.put(message.msg_data)
                        del self.partial_messages[hash]


            except Exception as e:
                print(f"[UDPCommunicator] Receiver error: {e}")

    def send(self, data: bytes, target_address=('127.0.0.1', PORT)):
        data_hash = hashlib.sha256(data).digest() # 32 byte hash

        total_chunks = (len(data) + CHUNK_SIZE - 1) // CHUNK_SIZE
        for chunk_number in range(total_chunks):
            start = chunk_number * CHUNK_SIZE
            end = start + CHUNK_SIZE
            chunk_data = data[start:end]

            chunk = DataChunk(data_hash, chunk_number, total_chunks, chunk_data)
            serialized = chunk.serialize()

            if len(serialized) > PACKET_LIMIT:
                raise ValueError("Serialized packet exceeds 16 KiB limit")

            if self.running:
                self.sender_sock.sendto(serialized, target_address)

    def stop(self):
        self.running = False
        self.sock.close()
        self.sender_sock.close()
