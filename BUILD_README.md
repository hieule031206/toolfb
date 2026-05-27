# 📦 Hướng dẫn xuất file EXE

## Yêu cầu
- Windows 10/11
- Đã cài đặt Python 3.10+
- Đã có thư mục `.venv` với đầy đủ dependencies

## Cách build (1 click)

### Bước 1: Chạy script build
```bash
build_exe.bat
```

Script sẽ:
1. Xóa build cũ
2. Chạy PyInstaller với file `FBAutoPost.spec`
3. Copy file exe vào thư mục `FBAutoPost_Portable/`
4. Tạo file `RUN.bat` để chạy

### Bước 2: Lấy file exe
Sau khi build xong:
- File exe: `FBAutoPost_Portable/FBAutoPost.exe`
- File chạy: `FBAutoPost_Portable/RUN.bat`

## Cấu trúc sau build
```
FBAutoPost_Portable/
├── FBAutoPost.exe    ← File chính (standalone)
├── RUN.bat           ← File chạy tiện lợi
└── (khi chạy sẽ tạo thêm)
    ├── chrome_profile/     ← Profile Chrome
    ├── saved_data/         ← Data đã lưu
    └── FB_Profile_Data/    ← Cache Facebook
```

## Chạy tool

### Cách 1: Chạy trực tiếp
```bash
FBAutoPost_Portable\FBAutoPost.exe
```

### Cách 2: Chạy qua RUN.bat (khuyến nghị)
```bash
FBAutoPost_Portable\RUN.bat
```

### Cách 3: Chạy với instance ID
```bash
FBAutoPost_Portable\RUN.bat 2
```

## Build thủ công (nếu cần)

```bash
# Kích hoạt venv
call .venv\Scripts\activate

# Cài pyinstaller nếu chưa có
pip install pyinstaller

# Build
pyinstaller FBAutoPost.spec --clean --noconfirm

# Lấy file exe từ thư mục dist/
```

## Troubleshooting

### Lỗi "missing module"
Thêm vào `hiddenimports` trong `FBAutoPost.spec`:
```python
hiddenimports=[
    'ten_module_thieu',
    ...
]
```

### File exe quá lớn
- Bật UPX nén: đã bật trong spec (`upx=True`)
- Thêm vào `excludes`: các module không cần

### Lỗi khi chạy exe
1. Kiểm tra log trong terminal
2. Chạy từ cmd để xem lỗi: `FBAutoPost.exe 1`
3. Kiểm tra thư mục `_internal` được tạo cùng exe
