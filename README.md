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
> Message code: _i_
> Header Data: Group ID  
> Message Data: None
**Response**
> Message code: _iR_ 
> Header Data: user: (_viewer_ or _ratifier_)
> Message Data: None 
### Ratify Message
**Query** 
> Message code: _mrat_
> Header Data: group_id: _group id (256bit)_
> Message Data: Message 
**Response**
> Message code: _mratR_ 
> Header Data: result: (_affirmative_ or _negative_) 
> Message Data: None 
### Send Message
**Query** 
> Message code: _smsg_
> Header Data: group_id: _group id (256bit)_
> Message Data: Message 
**Response**
> Message code: _smsgR_ 
> Header Data: result: (_affirmative_ or _negative_) 
> Message Data: None 
### Request Public Keys
### Requst Message DHT
