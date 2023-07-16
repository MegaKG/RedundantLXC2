#!/bin/sh
cp -v *.py RedundantLXC/usr/sbin/RedundantLXC/
dpkg-deb --build RedundantLXC
