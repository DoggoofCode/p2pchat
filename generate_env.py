import queue
import threading

from p2pchat.encryption.rsa_encryption import get_rsa_key
from p2pchat.response.responder import Responder

# Create RSA keys
keys = get_rsa_key()

# Create a test group
shutdown = threading.Event()
output: queue.Queue[bytes] = queue.Queue()
responder = Responder(shutdown, output, None)
group_id = b"TESTTESTTESTTEST"
responder.create_message_group(group_id)
