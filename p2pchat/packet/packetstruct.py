import pickle

class Message:
    def __init__(self, data:bytes, file_type:str) -> None:
        self.data = data
        self.file_type = file_type

class ReceivedChunk:
    def __init__(self, message_hash: bytes, chunk_number: int, total_chunks: int, data: bytes):
        self.message_hash = message_hash
        self.chunk_number = chunk_number
        self.total_chunks = total_chunks
        self.data = data

    def serialize(self) -> bytes:
        return pickle.dumps(self)

    @staticmethod
    def deserialize(data: bytes):
        return pickle.loads(data)

class ReceivedInformation:
    def __init__(self, total_chunks: int, message_hash: bytes):
        self.total_chunks = total_chunks
        self.message_hash = message_hash
        self.data_list: list[ReceivedChunk] = []

    def add_chunk(self, chunk: ReceivedChunk):
        self.data_list.append(chunk)

    @property
    def complete_data(self) -> bool:
        return len(self.data_list) == self.total_chunks

    @property
    def msg_data(self) -> bytes:
        if not self.complete_data:
            raise ValueError("Attempted to Request Incomplete data")
        sorted_chunks = sorted(self.data_list, key=lambda x: x.chunk_number)
        data = list(map(lambda chunk: chunk.data, sorted_chunks))
        return b''.join(data)
