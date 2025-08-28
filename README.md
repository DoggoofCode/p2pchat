# P2P Chat Platform
This project is a P2P chat platform. This uses a system of users and viewers in order to ratify messages that are send to the
group as a whole. This forces a clear chain of custody for primaries across the network minimising data loss along the way.


## Goals 
* Send packets between computers in local and other networks across the internet 
* End-to-End encryption between sources, using a DHT of the `Message()` to allow for members to see previously sent messages
* Send a variety of data types without a functional character or size limit for users.

## TODO
* Activated End-to-End encryption between sources with AES encryption (boring)
* Create the distinction between users and viewers
* Create a protocol for sending users and viewers data throughout the network
* Save chats between users and viewers
* Add full scale logging across the whole application
