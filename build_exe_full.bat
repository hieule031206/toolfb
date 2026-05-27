@echo off
chcp 65001 >nul
echo ===========================================
echo   BUILD FBAutoPost.exe (Full)
echo ===========================================
echo.

REM Xóa build cũ
echo [1/3] Xoa build cu...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build exe voi collect-all
echo [2/3] Dang build exe voi tat ca modules...
f:\toolfb\.venv\Scripts\pyinstaller.exe FBAutoPost.spec --clean --noconfirm ^
    --collect-all selenium ^
    --collect-all webdriver_manager ^
    --collect-all customtkinter

REM Kiểm tra kết quả
if exist "dist\FBAutoPost.exe" (
    echo [3/3] Build thanh cong!
    echo.
    
    if not exist FBAutoPost_Portable mkdir FBAutoPost_Portable
    copy /Y "dist\FBAutoPost.exe" "FBAutoPost_Portable\"
    
    echo ===========================================
    echo   BUILD HOAN TAT!
    echo ===========================================
    echo File: FBAutoPost_Portable\FBAutoPost.exe
    echo.
) else (
    echo [ERROR] Build that bai!
)
pause
