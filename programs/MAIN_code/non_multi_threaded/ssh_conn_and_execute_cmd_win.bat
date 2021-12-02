echo Connecting to pi from win

echo ip adress: %1
echo command file: %2

putty.exe -ssh pi@%1 -pw CW4A1panini -m %2