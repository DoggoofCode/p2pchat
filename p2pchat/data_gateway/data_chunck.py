import pickle

class Message:
    def __init__(self, data:bytes, file_type:str) -> None:
        self.data = data
        self.file_type = file_type

class DataChunk:
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
