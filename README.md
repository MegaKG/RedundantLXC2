# RedundantLXC2
A better version of a Redundant LXC Cluster

This program allows for the management of LXC clusters across multiple nodes with a shared storage medium.

Nodes can be assigned containers based on their Budget, Architecture and Current load.

The program will intelligently distribute containers across all nodes in the system, reassigning them in the event of failure.

All information is stored in a shared MYSQL backend server.

Tools are provided to manage the clustered containers.

