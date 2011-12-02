@echo off
:LOOP
set /p URL=please input URL:
(
    python -c "import redis,marshal;redis.Redis().lpush('download', marshal.dumps({'url':'%URL%'}))" 
)&& (
    echo commit url ok, your can commit another url
) || (
    echo commit url fail!!!
)
goto LOOP
@echo on