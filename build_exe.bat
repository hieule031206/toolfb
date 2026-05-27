@echo off
chcp 65001 >nul
echo ===========================================
echo   BUILD FBAutoPost.exe
echo ===========================================
echo.

REM Kích hoạt virtual environment
call .venv\Scripts\activate.bat

REM Xóa build cũ
echo [1/4] Xóa build cũ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build exe
echo [2/4] Đang build exe (có thể mất 2-3 phút)...
pyinstaller FBAutoPost.spec --clean --noconfirm

REM Kiểm tra kết quả
if exist "dist\FBAutoPost.exe" (
    echo [3/4] Build thành công!
    echo.
    echo [4/4] Copy file vào thư mục FBAutoPost_Portable...
    
    REM Tạo thư mục portable
    if not exist FBAutoPost_Portable mkdir FBAutoPost_Portable
    
    REM Copy exe và các file cần thiết
    copy /Y "dist\FBAutoPost.exe" "FBAutoPost_Portable\"
    
    REM Tạo file RUN.bat
    echo @echo off > "FBAutoPost_Portable\RUN.bat"
    echo chcp 65001 ^>nul >> "FBAutoPost_Portable\RUN.bat"
    echo echo Dang khoi dong FBAutoPost... >> "FBAutoPost_Portable\RUN.bat"
    echo start "" "%%~dp0FBAutoPost.exe" %%* >> "FBAutoPost_Portable\RUN.bat"
    
    echo.
    echo ===========================================
    echo   BUILD HOAN TAT!
    echo ===========================================
    echo.
    echo File exe: FBAutoPost_Portable\FBAutoPost.exe
    echo File chay: FBAutoPost_Portable\RUN.bat
    echo.
    echo De chay tool:
    echo   1. Mo thu muc FBAutoPost_Portable
    echo   2. Chay RUN.bat hoac FBAutoPost.exe
    echo.
    pause
) else (
    echo [ERROR] Build that bai!
    echo Kiem tra loi tren man hinh.
    pause
)
