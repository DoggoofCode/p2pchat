# P2P Chat Platform
This project is a P2P chat platform. This uses a system of users and viewers in order to ratify messages that are send to the
group as a whole. This forces a clear chain of custody for primaries across the network minimising data loss along the way.


## Goals
* ~Send packets between computers in local and other networks across the internet~
* End-to-End encryption between sources, using a DHT of the `Message()` to allow for members to see previously sent messages
* Send a variety of data types without a functional character or size limit for users.

## TODO
* Activated End-to-End encryption between sources with AES encryption (boring)
* Create the distinction between users and ratifiers
* Create a protocol for sending users and viewers data throughout the network
* Save chats between users and viewers
* Add full scale logging across the whole application

## Specifiations
Two different types of packet:
- Query: Queries query the recipient.
- Response: A response type only exist for all packet types to afferm or deny, or to send other information.

### Identify packet

**Query**

> Message code: _i_ \
> Header Data: Group ID \
> Message Data: None

**Response**

> Message code: _iR_ \
> Header Data: user: (_viewer_ or _ratifier_) \
> Message Data: None

### Ratify Message

**Query**

> Message code: _mrat_ \
> Header Data: group_id: _group id (256bit)_ \
> Message Data: Message

**Response**

> Message code: _mratR_ \
> Header Data: result: (_affirmative_ or _negative_) \
> Message Data: None

### Send Message

**Query**

> Message code: _smsg_ \
> Header Data: group_id: _group id (256bit)_ \
> Message Data: Message

**Response**

> Message code: _smsgR_ \
> Header Data: result: (_affirmative_ or _negative_) \
> Message Data: None

### Request Public Keys

**Query**

> Message code: _pkt_ \
> Header Data: group_id: _group id (256bit)_ \
> Message Data: None

**Response**

> Message code: _pktR_ \
> Header Data: result: (_affirmative_ or _negative_) \
> Message Data: Key Table or None

### Requst Message DHT

**Query**

> Message code: _dht_ \
> Header Data: group_id: _group id (256bit)_ \
> Message Data: None

**Response**

> Message code: _dhtR_ \
> Header Data: result: (_affirmative_ or _negative_) \
> Message Data: DHT Table or None

## Packet Specifiations

```json
{
    "message_hash": "B64 Encoded String", // Hash of the concatonations of all the artifact hashes. Intended as a unique identifier for the message.
    "aes_key": "B64 Encoded String", // RSA Encrypted AES Key for all artifact data
    "iv": "B64 Encoded String", // Initialization Vector for AES Key
    "signature": "B64 Encoded String", // RSA Signature of the message hash. Undiable proof of authenticity.
    "message": {
      "message_type": "String", // Outlined in specifications, one of the message packet types
      "time_stamp": 0000, // Unix timestamp of the message, for archival purposes only.
      "author": "B64 Encoded String", // B64 Encoded String of the author's public key.
      "ref_hash": "B64 Encoded String", // None or Hash String: None normally, when the message type edits another message, when the message type edits another message, the hash of the message being edited.
      "headers": { // These are generic headers for response
        "identifier": "user", // User or Viewer based on their position in the group
        "response_code": 0 // Positive (0) or negative response (Any other response)
      },
      "artifact": {
        "type": "String", // Type of artifact, one of the artifact types, currently "txt", "md", "png"
        "data": "B64 Encoded String", // B64 Encoded String of the artifact data encrypted with AES key
        "hash": "B64 Encoded String" // Hash of the artifact data **encrypted with AES key**
      }
    }
}
```

> Note: Later, more formats will be used, currently the core does not supported edit or delete messages for complexity reasons. For now all RSA signatures will be omitted by using None because **I am lazy**
