start "redis server" "%~dp0redis-server\redis-server.exe"
start "downloader" python.exe downloader.py 20
start "parser" python parser.py
start "saver" python saver.py
rem start "saveaser" python saver.py