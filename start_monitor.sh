#!/bin/bash
# SubWatch startup script
# Update the path below to match your installation directory
cd /mnt/c/code/SubWatch || exit
python3 main.py >> monitor.log 2>&1
