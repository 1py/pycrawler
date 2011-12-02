cd /d "%~dp0redis-server" && title redis-server
if exist "dump.rdb" (del /f dump.rdb)
.\redis-server.exe