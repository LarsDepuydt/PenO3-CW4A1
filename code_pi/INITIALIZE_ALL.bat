echo Initializing and opening web UI

# <start> means that it will start a new process -> doesn't wait for it to finish before proceding.

start "DontGetRobbedinator | Web App" python ../../web_ui/web_streaming.py

start "DontGetRobbedinator" "http://127.0.0.1:5000"
