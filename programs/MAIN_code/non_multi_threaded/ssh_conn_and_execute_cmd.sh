#!/bin/sh

# Input argument = $1
lxterminal --title="HELPER TERMINAL" --command="sshpass -p 'CW4A1panini' ssh pi@169.254.165.116 '$1'; sleep 5000"