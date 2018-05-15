@echo off

if "%1" == "h" goto begin
rem hide cmd window
mshta vbscript:createobject("wscript.shell").run("%~nx0 h",0)(window.close)&&exit

:begin
pipenv run python main.py
