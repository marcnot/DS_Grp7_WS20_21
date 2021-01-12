# DS_Grp7_WS20_21

Client-server chat application

The idea of the following project is to develop a client-server application with distributed properties according to the given requirements of a distributed system.

For our approach to these requirements, an n-sized number of clients with a network consisting of a lead server and its replicas will be implemented. The clients can communicate with each other via text messages and reply to received messages. Before an individual client can send a message to the network, it must give itself a username. Messages cannot be sent directly to individual clients but are always sent to the entire network. The messages are displayed in chronological order at the clients.  

The clients' text messages are processed by a lead server. This server has n-number of replica entities. The lead server will coordinate the messages and sent to the other clients. The remaining servers serve as replica to substitute it in case of an error or failure.  
