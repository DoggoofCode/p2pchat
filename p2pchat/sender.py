from data_gateway.data_sender import UDPCommunicator
from message_encryption import keys, Message, MessagePacket, MsgData
from message_encryption.encryption_keys import RSAEncryptionKeys
import threading, time


def incoming(communicator: UDPCommunicator, encrypt: RSAEncryptionKeys):
    while True:
        new_msg = communicator.reassembled_messages.get()
        if new_msg is None:
            continue
        # Decrypt
        msg: MessagePacket = MessagePacket.deserialize(new_msg)
        msg.decrypt(encrypt.private_key)
        print(msg)



def main():

    encryption_key = keys.verify(
        "..\\encryption_info\\keys\\public.pem",
        "..\\encryption_info\\keys\\private.pem"
    )
    print("encryption key is: {}".format(encryption_key))

    comm = UDPCommunicator()
    responder = threading.Thread(target=incoming, args=(comm, encryption_key))
    responder.start()

    comm.send(
        MessagePacket(
            Message(
                "send-msg",
                message_data=[
                    MsgData(
                        b'Wsg gng',
                        "txt"
                    )
                ]
            ),
            encryption_key.public_key
        ).serialize()
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        comm.stop()
        print("[Main] Shutdown complete.")
        raise Exception("Shutdown complete.")


if __name__ == '__main__':
    main()