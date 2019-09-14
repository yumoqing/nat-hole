# NAT Hole

This module make p2p connect

## Outside server

there is a server on internet, each p2p node heart beat with this server

when node A want to connect to node B, it talk server its want to connect to node b, and it want b to connect to its port.

then server reply A with node B's ip and port on internet, and forward A's info to node B

A connnect to node B's ip and port

B use the info transfered by server, to connect node A's ip and port. then the connection built.




