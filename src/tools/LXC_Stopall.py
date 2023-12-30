#!/usr/bin/env python3
import lxc

Containers = lxc.list_containers()
for i in Containers:
    print(i)
    C = lxc.Container(i)
    C.stop()