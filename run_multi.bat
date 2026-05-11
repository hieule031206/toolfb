@echo off
chcp 65001 >nul
echo ========================================
echo  FB Auto Post Pro - Multi Instance Runner
echo ========================================
echo.

if "%~1"=="" (
    echo Cách dùng: run_multi.bat [số_lượng_instance]
    echo Ví dụ: run_multi.bat 2
echo.
    echo Đang chạy mặc định 2 instance...
    set COUNT=2
) else (
    set COUNT=%~1
)

echo Chạy %COUNT% instance...
echo.

setlocal enabledelayedexpansion
for /L %%i in (1,1,%COUNT%) do (
    echo Khởi động Instance %%i...
    start "FB Auto Post - Tab %%i" cmd /c "cd /d "%~dp0" && .venv\Scripts\python.exe giaodien.py %%i"
    timeout /t 2 /nobreak >nul
)

echo.
echo Đã khởi động xong %COUNT% instance!
echo Mỗi instance có profile và port riêng biệt.
pause
