echo Connecting to pi from win

echo %1
echo in script: %2

putty.exe -ssh pi@%1 -pw CW4A1panini -m %2