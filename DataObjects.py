#!/usr/bin/env python3
from dataclasses import dataclass

@dataclass
class Container:
    ID: int
    Name: str
    Priority: int
    Cost: int
    Zone: int
    Arch: str

@dataclass
class Node:
    ID: int
    Name: str
    Budget: int
    Arch: str

@dataclass
class Zone:
    ID: int
    Name: str
    Nodes: list