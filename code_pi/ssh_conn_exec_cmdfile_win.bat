echo Trying to connect to Pi via SSH(Putty)

echo ip adress: %1
echo command file: %2

start "Remote Terminal" putty.exe -ssh pi@%1 -pw CW4A1panini -m %2