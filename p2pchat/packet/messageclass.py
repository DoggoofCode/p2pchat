from typing import Literal 

MESSAGE_CODES = Literal["i", "mrat", "smsg", "pkt", "dht", "iR", "mratR", "smsgR", "pktR", "dhtR"]

class Message:
    message_code: MESSAGE_CODES
    groupID: int
    response_text: str
    def __init__(self, message_code: MESSAGE_CODES, groupID:int):
        self.message_code = message_code
        self.groupID = groupID
    
    def set_response(self, response: str):
        self.response_text = response

    def __repr__(self):
        return f"Message(code:{self.message_code}, txt:{self.response_text})"
