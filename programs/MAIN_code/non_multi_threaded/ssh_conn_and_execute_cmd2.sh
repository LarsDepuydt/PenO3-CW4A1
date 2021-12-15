#!/bin/sh

echo $1
# Input argument = $1
sshpass -p 'CW4A1panini' ssh pi@169.254.165.116 '$1'; sleep 5

echo here