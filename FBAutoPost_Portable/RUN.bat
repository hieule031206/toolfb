@echo off 
chcp 65001 >nul 
echo Dang khoi dong FBAutoPost... 
start "" "%~dp0FBAutoPost.exe" %* 
