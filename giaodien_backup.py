import customtkinter as ctk

import threading

import time

import random

import sys

from datetime import datetime

from tkinter import filedialog

from pathlib import Path

from backend import FacebookBot



# Kiểm tra và import clipboard support (optional)

try:

    import win32clipboard

    from PIL import Image, ImageGrab

    CLIPBOARD_SUPPORT = True

except ImportError:

    CLIPBOARD_SUPPORT = False



class TabContent:

    """Đại diện cho 1 sub-tab với content, images, links"""

    def __init__(self):

        self.content = ""

        self.images = []

        self.links = ""

        self.ui_refs = {}  # Tham chiếu đến UI widgets

        self.is_completed = False



class ProfessionalGroupPost(ctk.CTk):

    def __init__(self, instance_id=1):

        super().__init__()

        self.instance_id = instance_id

        self.title(f"FB Auto Post Pro 2026 - Chrome {instance_id}")

        self.geometry("1200x800")

        self.configure(fg_color="#F0F2F5")

        

        self.bot = FacebookBot(instance_id=instance_id)

        self.is_running = False

        self.tabs_data = []  # List[TabContent]

        self.current_tab_index = 0

        self.tabview = None

        

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        

        # Layout chính

        self.grid_columnconfigure(0, weight=1)

        self.grid_rowconfigure(0, weight=0)  # Header

        self.grid_rowconfigure(1, weight=1)  # Tabview

        self.grid_rowconfigure(2, weight=0)  # Controls

        

        self._create_header()

        self._create_tabview()

        self._create_controls()

        

        # Thêm sub-tab đầu tiên

        self.add_sub_tab()

    

    def _create_header(self):

        """Tạo header với nút mở Chrome"""

        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10)

        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        

        ctk.CTkLabel(header, text=f"🌐 Chrome Instance {self.instance_id}", 

                    font=("Arial", 16, "bold")).pack(side="left", padx=20, pady=15)

        

        self.btn_browser = ctk.CTkButton(header, text="▶ MỞ TRÌNH DUYỆT",

                                        command=self.open_chrome, height=40,

                                        font=("Arial", 12, "bold"), fg_color="#1877F2")

        self.btn_browser.pack(side="right", padx=20, pady=15)

    

    def _create_tabview(self):

        """Tạo tabview chứa các sub-tabs"""

        # Frame chứa tabview + nút +

        container = ctk.CTkFrame(self, fg_color="transparent")

        container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        container.grid_columnconfigure(0, weight=1)

        container.grid_rowconfigure(0, weight=1)

        

        self.tabview = ctk.CTkTabview(container, fg_color="white", corner_radius=15)

        self.tabview.grid(row=0, column=0, sticky="nsew")

        

        # Nút thêm tab (+)

        self.btn_add_tab = ctk.CTkButton(container, text="➕", width=40, height=40,

                                        command=self.add_sub_tab, font=("Arial", 16))

        self.btn_add_tab.grid(row=0, column=1, padx=(10, 0))

    

    def _create_controls(self):

        """Tạo controls chạy campaign"""

        controls = ctk.CTkFrame(self, fg_color="white", corner_radius=10)

        controls.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")

        

        # Progress label

        self.lbl_progress = ctk.CTkLabel(controls, text="Sẵn sàng", 

                                        font=("Arial", 12), text_color="gray")

        self.lbl_progress.pack(side="left", padx=20, pady=15)

        

        # Nút chạy tất cả sub-tabs

        self.btn_run_all = ctk.CTkButton(controls, text="🚀 CHẠY TẤT CẢ SUB-TABS",

                                        command=self.run_all_tabs, height=45,

                                        font=("Arial", 14, "bold"), fg_color="#28a745")

        self.btn_run_all.pack(side="right", padx=20, pady=15)

        

        # Switch spin

        self.sw_spin = ctk.CTkSwitch(controls, text="Thêm ID tránh trùng")

        self.sw_spin.pack(side="right", padx=20, pady=15)



        self.btn_browser = ctk.CTkButton(self.left_panel, text="🌐 1. MỞ TRÌNH DUYỆT",

                                        command=self.open_chrome, height=45, font=("Arial", 13, "bold"))

        self.btn_browser.pack(fill="x", padx=20, pady=20)



        ctk.CTkLabel(self.left_panel, text="📝 Nội dung bài viết:").pack(anchor="w", padx=20)

        

        # Frame chứa textbox + tooltip

        content_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")

        content_frame.pack(fill="x", padx=20, pady=5)

        

        self.txt_content = ctk.CTkTextbox(content_frame, height=120, border_width=1)

        self.txt_content.pack(fill="x")

        

        # Tooltip hướng dẫn

        tooltip_text = "💡 Ctrl+Click để chọn ảnh | Ctrl+Shift+V để dán ảnh từ clipboard" if CLIPBOARD_SUPPORT else "💡 Ctrl+Click để chọn ảnh nhanh"

        ctk.CTkLabel(content_frame, text=tooltip_text, font=("Arial", 10), text_color="gray").pack(anchor="e", padx=5)

        

        # Bind Ctrl+Click để chọn ảnh nhanh (tránh conflict với edit)

        self.txt_content.bind("<Control-Button-1>", lambda e: self.select_images())

        # Bind Ctrl+Shift+V để paste ảnh từ clipboard (nếu có hỗ trợ)

        if CLIPBOARD_SUPPORT:

            self.txt_content.bind("<Control-Shift-KeyPress-v>", lambda e: self.paste_images_from_clipboard())



        # --- CHỌN ẢNH ---

        self.image_paths = []

        self.lbl_images = ctk.CTkLabel(self.left_panel, text="📷 Chưa chọn ảnh nào", text_color="gray")

        self.lbl_images.pack(anchor="w", padx=20, pady=(5, 0))

        

        # Frame chứa 2 nút ảnh

        img_btn_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")

        img_btn_frame.pack(fill="x", padx=20, pady=5)

        

        self.btn_select_images = ctk.CTkButton(

            img_btn_frame, text="📎 Chọn ảnh",

            command=self.select_images, height=32, font=("Arial", 12),

            fg_color="#28a745", hover_color="#218838", width=150

        )

        self.btn_select_images.pack(side="left", padx=(0, 10))

        

        self.btn_clear_images = ctk.CTkButton(

            img_btn_frame, text="🗑️ Xóa ảnh",

            command=self.clear_images, height=32, font=("Arial", 12),

            fg_color="#dc3545", hover_color="#c82333", width=100

        )

        self.btn_clear_images.pack(side="left")



        ctk.CTkLabel(self.left_panel, text="🔗 Link nhóm (mỗi dòng 1 link):").pack(anchor="w", padx=20, pady=(10, 0))

        self.txt_groups = ctk.CTkTextbox(self.left_panel, height=150, border_width=1)

        self.txt_groups.pack(fill="x", padx=20, pady=5)



        self.sw_spin = ctk.CTkSwitch(self.left_panel, text="Tự động thêm ID tránh trùng (Spin)")

        self.sw_spin.pack(padx=20, pady=10, anchor="w")



        self.btn_run = ctk.CTkButton(self.left_panel, text="🚀 BẮT ĐẦU ĐĂNG",

                                    fg_color="#1877F2", height=50, font=("Arial", 15, "bold"),

                                    command=self.toggle_process)

        self.btn_run.pack(fill="x", padx=20, pady=20)



        # --- RIGHT PANEL (LOG) ---

        self.right_panel = ctk.CTkFrame(self, fg_color="white", corner_radius=15)

        self.right_panel.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

       

        ctk.CTkLabel(self.right_panel, text="📊 NHẬT KÝ HOẠT ĐỘNG", font=("Arial", 14, "bold")).pack(pady=10)

        self.log_view = ctk.CTkScrollableFrame(self.right_panel, fg_color="#F8FAFC")

        self.log_view.pack(fill="both", expand=True, padx=10, pady=10)



    def open_chrome(self):

        # Fix #1: chạy trên thread riêng, không block tkinter

        self.btn_browser.configure(state="disabled", text="⏳ Đang mở...")

        def _open():

            msg = self.bot.open_for_login()

            self.after(0, lambda: self.add_log("Hệ thống", msg))

            self.after(0, lambda: self.btn_browser.configure(state="normal", text="🌐 1. MỞ TRÌNH DUYỆT"))

        threading.Thread(target=_open, daemon=True).start()



    def _on_closing(self):

        # Fix #4: đảm bảo driver.quit() trước khi tắt → cookie flush xuống đĩa

        self.is_running = False

        self.bot.quit()

        self.destroy()



    def select_images(self, initial_paths=None):

        """Mở dialog chọn ảnh. Nếu initial_paths có giá trị, thêm vào danh sách hiện có."""

        files = filedialog.askopenfilenames(

            title="Chọn ảnh đính kèm (Ctrl/Shift để chọn nhiều)",

            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.webp"), ("All files", "*.*")],

            initialdir="~/Pictures"

        )

        if files:

            if initial_paths:

                self.image_paths.extend(initial_paths)

            self.image_paths.extend(files)

            self._update_image_label()

        return files



    def paste_images_from_clipboard(self):

        """Paste ảnh từ clipboard - hỗ trợ đường dẫn file hoặc ảnh bitmap"""

        try:

            import win32clipboard

            from PIL import Image, ImageGrab

            import io

            import tempfile

            import os

            

            # Thử lấy đường dẫn file từ clipboard (khi copy file trong Explorer)

            win32clipboard.OpenClipboard()

            try:

                # Thử định dạng HDROP (file drop)

                data = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)

                win32clipboard.CloseClipboard()

                

                # data là list các đường dẫn file

                image_files = [f for f in data if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'))]

                if image_files:

                    self.image_paths.extend(image_files)

                    self._update_image_label()

                    self.add_log("Hệ thống", f"Đã dán {len(image_files)} ảnh từ clipboard")

                    return

            except:

                win32clipboard.CloseClipboard()

            

            # Thử lấy ảnh bitmap từ clipboard (khi copy ảnh từ app khác)

            try:

                img = ImageGrab.grabclipboard()

                if isinstance(img, Image.Image):

                    # Lưu ảnh tạm

                    temp_dir = tempfile.gettempdir()

                    temp_path = os.path.join(temp_dir, f"pasted_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

                    img.save(temp_path, "PNG")

                    self.image_paths.append(temp_path)

                    self._update_image_label()

                    self.add_log("Hệ thống", "Đã dán ảnh từ clipboard")

                    return

            except:

                pass

                

            self.add_log("Hệ thống", "Clipboard không chứa ảnh hoặc đường dẫn file ảnh")

        except ImportError:

            self.add_log("Hệ thống", "Lỗi: Cần cài pywin32 và Pillow để paste ảnh (pip install pywin32 pillow)")

        except Exception as e:

            self.add_log("Hệ thống", f"Lỗi paste ảnh: {str(e)[:100]}")



    def clear_images(self):

        """Xóa tất cả ảnh đã chọn"""

        self.image_paths = []

        self._update_image_label()

        self.add_log("Hệ thống", "Đã xóa tất cả ảnh đã chọn")



    def _update_image_label(self):

        """Cập nhật label hiển thị ảnh đã chọn"""

        if self.image_paths:

            count = len(self.image_paths)

            names = ", ".join([Path(f).name for f in self.image_paths[:3]])

            if count > 3:

                names += f" và {count - 3} ảnh khác"

            self.lbl_images.configure(text=f"📷 Đã chọn {count} ảnh: {names}", text_color="#28a745")

        else:

            self.lbl_images.configure(text="📷 Chưa chọn ảnh nào", text_color="gray")



    def add_log(self, target, message):

        time_str = datetime.now().strftime("%H:%M:%S")

        color = "#2ecc71" if "Thành công" in message else "#e74c3c" if "Lỗi" in message else "#34495e"

       

        frame = ctk.CTkFrame(self.log_view, fg_color="transparent")

        frame.pack(fill="x", pady=2)

       

        lbl = ctk.CTkLabel(frame, text=f"[{time_str}] {target}: {message}",

                           font=("Segoe UI", 12), text_color=color, wraplength=450, justify="left")

        lbl.pack(side="left", padx=5)

        self.log_view._parent_canvas.yview_moveto(1.0)



    def toggle_process(self):

        if not self.is_running:

            self.is_running = True

            self.btn_run.configure(text="🛑 DỪNG LẠI", fg_color="#d32f2f")

            threading.Thread(target=self.run_campaign, daemon=True).start()

        else:

            self.is_running = False

            self.btn_run.configure(text="🚀 BẮT ĐẦU ĐĂNG", fg_color="#1877F2")



    def run_campaign(self):

        urls = [u.strip() for u in self.txt_groups.get("1.0", "end").strip().split('\n') if u.strip()]

        content = self.txt_content.get("1.0", "end").strip()

        is_spin = self.sw_spin.get()

        img_count = len(self.image_paths)



        if not urls or not content:

            self.after(0, lambda: self.add_log("Hệ thống", "Lỗi: Thiếu nội dung hoặc link!"))

            self.is_running = False

            self.after(0, lambda: self.btn_run.configure(text="🚀 BẮT ĐẦU ĐĂNG", fg_color="#1877F2"))

            return



        self.after(0, lambda: self.add_log("Hệ thống", f"Bắt đầu đăng {len(urls)} nhóm, {img_count} ảnh, Tab {self.instance_id}"))



        for i, url in enumerate(urls):

            if not self.is_running: 

                self.after(0, lambda: self.add_log("Hệ thống", "Đã dừng chiến dịch"))

                break

           

            self.after(0, lambda u=url: self.add_log(u, f"[{i+1}/{len(urls)}] Đang đăng..."))

           
            try:

                success, result_msg = self.bot.post_to_target(url, content, is_spin, self.image_paths)

                self.after(0, lambda u=url, m=result_msg: self.add_log(u, m))

            except Exception as e:

                self.after(0, lambda u=url, e=str(e): self.add_log(u, f"Lỗi exception: {e[:100]}"))

           

            if self.is_running and i != len(urls) - 1:

                delay = random.randint(30, 60)

                self.after(0, lambda d=delay: self.add_log("Hệ thống", f"Nghỉ {d}s trước bài tiếp theo..."))

                time.sleep(delay)



        self.is_running = False

        self.after(0, lambda: self.btn_run.configure(text="🚀 BẮT ĐẦU ĐĂNG", fg_color="#1877F2"))

        self.after(0, lambda: self.add_log("Hệ thống", f"Hoàn thành chiến dịch Tab {self.instance_id}!"))



if __name__ == "__main__":

    # Nhận instance_id từ dòng lệnh: python giaodien.py 2

    instance_id = 1

    if len(sys.argv) > 1:

        try:

            instance_id = int(sys.argv[1])

        except ValueError:

            pass

    

    app = ProfessionalGroupPost(instance_id=instance_id)

    app.mainloop()