import customtkinter as ctk
import threading
import time
import random
import sys
import json
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


class SubTabData:
    """Dữ liệu của 1 sub-tab"""
    def __init__(self, name):
        self.name = name
        self.content = ""
        self.images = []
        self.links = ""
        self.is_completed = False
        self.ui_refs = {}


class ProfessionalGroupPost(ctk.CTk):
    def __init__(self, instance_id=1):
        super().__init__()
        self.instance_id = instance_id
        self.title(f"FB Auto Post Pro - Chrome {instance_id}")
        self.geometry("1400x850")
        self.configure(fg_color="#F0F2F5")
        
        self.bot = FacebookBot(instance_id=instance_id)
        self.is_running = False
        self.sub_tabs = []  # List[SubTabData]
        self.current_subtab_index = -1
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Content
        self.grid_rowconfigure(2, weight=0)  # Footer
        
        self._create_header()
        self._create_main_content()
        self._create_footer()
        
        # Thêm sub-tab đầu tiên
        self.add_sub_tab()
        
        # Load data đã lưu (nếu có)
        self.after(500, self._load_data_async)
    
    def _create_header(self):
        """Header với nút mở Chrome và thông tin"""
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        header.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        
        # Tiêu đề instance
        ctk.CTkLabel(header, text=f"🌐 Chrome Instance {self.instance_id}", 
                    font=("Arial", 18, "bold"), text_color="#1877F2").pack(side="left", padx=20, pady=15)
        
        # Trạng thái
        self.lbl_status = ctk.CTkLabel(header, text="Sẵn sàng", 
                                      font=("Arial", 12), text_color="gray")
        self.lbl_status.pack(side="left", padx=20, pady=15)
        
        # Nút mở Chrome
        self.btn_browser = ctk.CTkButton(header, text="▶ MỞ CHROME", command=self.open_chrome,
                                        height=40, font=("Arial", 12, "bold"), fg_color="#1877F2")
        self.btn_browser.pack(side="right", padx=20, pady=15)
    
    def _create_main_content(self):
        """Khu vực chính với tabview"""
        # Frame chứa tabview và nút điều khiển tab
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, padx=15, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Tab bar tùy chỉnh (dùng frame thay vì CTkTabview để có nút x trên mỗi tab)
        self.tab_bar = ctk.CTkFrame(main_frame, fg_color="transparent", height=40)
        self.tab_bar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Nút thêm tab
        self.btn_add_tab = ctk.CTkButton(self.tab_bar, text="➕ Thêm", width=80, height=32,
                                        command=self.add_sub_tab, font=("Arial", 11),
                                        fg_color="#28a745", hover_color="#218838")
        self.btn_add_tab.pack(side="left", padx=(0, 10))
        
        # Container cho sub-tabs
        self.tab_container = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=15)
        self.tab_container.grid(row=1, column=0, sticky="nsew")
        self.tab_container.grid_columnconfigure(0, weight=1)
        self.tab_container.grid_rowconfigure(0, weight=1)
        
        # Frame chứa các sub-tab frames
        self.subtab_frames = []
    
    def _create_footer(self):
        """Footer với controls chạy"""
        footer = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        footer.grid(row=2, column=0, padx=15, pady=(10, 15), sticky="ew")
        
        # Switch spin
        self.sw_spin = ctk.CTkSwitch(footer, text="Thêm ID tránh trùng")
        self.sw_spin.pack(side="left", padx=20, pady=15)
        
        # Progress
        self.lbl_progress = ctk.CTkLabel(footer, text="0 sub-tabs | 0 hoàn thành", 
                                      font=("Arial", 12), text_color="gray")
        self.lbl_progress.pack(side="left", padx=20, pady=15)
        
        # Nút chạy tất cả
        self.btn_run_all = ctk.CTkButton(footer, text="🚀 CHẠY TẤT CẢ SUB-TABS", 
                                        command=self.run_all_subtabs,
                                        height=45, font=("Arial", 14, "bold"),
                                        fg_color="#dc3545", hover_color="#c82333")
        self.btn_run_all.pack(side="right", padx=20, pady=15)
    
    def add_sub_tab(self):
        """Thêm sub-tab mới"""
        idx = len(self.sub_tabs)
        tab_name = f"Nội dung {idx + 1}"
        
        # Tạo data
        tab_data = SubTabData(tab_name)
        self.sub_tabs.append(tab_data)
        
        # Tạo nút tab trên tab bar
        tab_btn_frame = ctk.CTkFrame(self.tab_bar, fg_color="#e0e0e0", corner_radius=8, width=120, height=32)
        tab_btn_frame.pack(side="left", padx=2, pady=3)
        tab_btn_frame.pack_propagate(False)
        
        # Nút chuyển tab
        btn_switch = ctk.CTkButton(tab_btn_frame, text=tab_name, width=80, height=28,
                                  font=("Arial", 11), fg_color="transparent", hover_color="#d0d0d0",
                                  text_color="black", command=lambda i=idx: self.switch_to_subtab(i))
        btn_switch.pack(side="left", padx=2)
        
        # Nút xóa (nếu có nhiều hơn 1 tab)
        if len(self.sub_tabs) > 1:
            btn_close = ctk.CTkButton(tab_btn_frame, text="×", width=24, height=28,
                                     font=("Arial", 12, "bold"), fg_color="transparent",
                                     hover_color="#ff6b6b", text_color="#666",
                                     command=lambda i=idx: self.remove_sub_tab(i))
            btn_close.pack(side="right", padx=2)
        
        # Tạo frame cho sub-tab này
        frame = ctk.CTkFrame(self.tab_container, fg_color="white")
        frame.grid_columnconfigure(0, weight=1)  # Left - Content
        frame.grid_columnconfigure(1, weight=1)  # Right - Links
        frame.grid_rowconfigure(0, weight=1)       # Row 0: Content + Links (expand)
        frame.grid_rowconfigure(1, weight=0)       # Row 1: Images (fixed)
        
        # === ROW 0, COL 0: CONTENT (BÊN TRÁI) ===
        content_frame = ctk.CTkFrame(frame, fg_color="white", corner_radius=10, border_width=2, border_color="#dee2e6")
        content_frame.grid(row=0, column=0, padx=(15, 8), pady=15, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=0)
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_rowconfigure(2, weight=0)
        
        ctk.CTkLabel(content_frame, text="📝 NỘI DUNG BÀI VIẾT", 
                    font=("Arial", 14, "bold"), text_color="#1877F2").grid(row=0, column=0, sticky="w", padx=15, pady=(12, 8))
        
        txt_content = ctk.CTkTextbox(content_frame, height=200, border_width=1, font=("Arial", 12))
        txt_content.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        txt_content.insert("1.0", tab_data.content)
        
        # Tooltip
        tooltip = "💡 Ctrl+Click: chọn ảnh | Ctrl+Shift+V: dán ảnh" if CLIPBOARD_SUPPORT else "💡 Ctrl+Click: chọn ảnh"
        ctk.CTkLabel(content_frame, text=tooltip, font=("Arial", 10), text_color="gray").grid(row=2, column=0, sticky="e", padx=15, pady=(0, 10))
        
        # Bind
        txt_content.bind("<Control-Button-1>", lambda e, t=idx: self.select_images_for_tab(t))
        if CLIPBOARD_SUPPORT:
            txt_content.bind("<Control-Shift-KeyPress-v>", lambda e, t=idx: self.paste_images_for_tab(t))
        
        # === ROW 0, COL 1: LINKS (BÊN PHẢI) ===
        links_frame = ctk.CTkFrame(frame, fg_color="white", corner_radius=10, border_width=2, border_color="#dee2e6")
        links_frame.grid(row=0, column=1, padx=(8, 15), pady=15, sticky="nsew")
        links_frame.grid_columnconfigure(0, weight=1)
        links_frame.grid_rowconfigure(0, weight=0)
        links_frame.grid_rowconfigure(1, weight=0)
        links_frame.grid_rowconfigure(2, weight=1)  # Textarea expand
        links_frame.grid_rowconfigure(3, weight=0)  # Status
        
        ctk.CTkLabel(links_frame, text="🔗 LINK NHÓM FACEBOOK", 
                    font=("Arial", 14, "bold"), text_color="#dc3545").grid(row=0, column=0, sticky="w", padx=15, pady=(12, 5))
        
        ctk.CTkLabel(links_frame, text="Mỗi dòng 1 link", 
                    font=("Arial", 11), text_color="gray").grid(row=1, column=0, sticky="w", padx=15, pady=(0, 5))
        
        txt_links = ctk.CTkTextbox(links_frame, height=200, border_width=1, font=("Arial", 11))
        txt_links.grid(row=2, column=0, sticky="nsew", padx=15, pady=5)
        txt_links.insert("1.0", tab_data.links)
        
        # Status
        status_frame = ctk.CTkFrame(links_frame, fg_color="#f8f9fa", corner_radius=5, height=40)
        status_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(8, 12))
        status_frame.grid_columnconfigure(0, weight=1)
        
        lbl_status = ctk.CTkLabel(status_frame, text="⏳ Chưa chạy", 
                                 font=("Arial", 12), text_color="#6c757d")
        lbl_status.grid(row=0, column=0, sticky="w", padx=10, pady=8)
        
        # === ROW 1: IMAGES (DƯỚI CÙNG, FULL WIDTH) ===
        images_frame = ctk.CTkFrame(frame, fg_color="#f8f9fa", corner_radius=10, border_width=2, border_color="#dee2e6")
        images_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        
        ctk.CTkLabel(images_frame, text="📷 ẢNH ĐÍNH KÈM", 
                    font=("Arial", 14, "bold"), text_color="#28a745").pack(anchor="w", padx=15, pady=(12, 8))
        
        lbl_images = ctk.CTkLabel(images_frame, text="Chưa chọn ảnh nào", 
                                 text_color="#6c757d", font=("Arial", 12))
        lbl_images.pack(anchor="w", padx=15, pady=(3, 10))
        
        img_btn_frame = ctk.CTkFrame(images_frame, fg_color="transparent")
        img_btn_frame.pack(fill="x", padx=15, pady=(3, 15))
        
        def make_select_handler(tab_idx):
            return lambda: self.select_images_for_tab(tab_idx)
        
        def make_clear_handler(tab_idx):
            return lambda: self.clear_images_for_tab(tab_idx)
        
        # Nút chọn ảnh
        btn_select = ctk.CTkButton(img_btn_frame, text="📎 CHỌN ẢNH", width=140, height=40,
                                  command=make_select_handler(idx),
                                  fg_color="#1877F2", hover_color="#166fe5",
                                  font=("Arial", 13, "bold"), corner_radius=8)
        btn_select.pack(side="left", padx=(0, 15), pady=5)
        
        # Nút xóa ảnh
        btn_clear = ctk.CTkButton(img_btn_frame, text="🗑️ XÓA", width=100, height=40,
                                 command=make_clear_handler(idx),
                                 fg_color="#dc3545", hover_color="#c82333",
                                 font=("Arial", 13), corner_radius=8)
        btn_clear.pack(side="left", pady=5)
        
        # Lưu refs
        tab_data.ui_refs = {
            'frame': frame,
            'tab_btn_frame': tab_btn_frame,
            'txt_content': txt_content,
            'txt_links': txt_links,
            'lbl_images': lbl_images,
            'lbl_status': lbl_status,
            'btn_switch': btn_switch
        }
        
        self.subtab_frames.append(frame)
        
        # Chuyển đến tab mới
        self.switch_to_subtab(idx)
        self._update_progress()
    
    def switch_to_subtab(self, index):
        """Chuyển đến sub-tab chỉ định"""
        if index < 0 or index >= len(self.sub_tabs):
            return
        
        # Ẩn tất cả
        for i, frame in enumerate(self.subtab_frames):
            frame.grid_forget()
            # Reset style nút
            if i < len(self.sub_tabs):
                btn = self.sub_tabs[i].ui_refs.get('tab_btn_frame')
                if btn:
                    btn.configure(fg_color="#e0e0e0")
        
        # Hiện tab được chọn
        self.subtab_frames[index].grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.current_subtab_index = index
        
        # Highlight nút
        btn_frame = self.sub_tabs[index].ui_refs.get('tab_btn_frame')
        if btn_frame:
            btn_frame.configure(fg_color="#1877F2")  # Màu xanh active
        
        self._update_progress()
    
    def remove_sub_tab(self, index):
        """Xóa sub-tab (phải còn ít nhất 1 tab)"""
        if len(self.sub_tabs) <= 1:
            self._show_status("Phải giữ ít nhất 1 sub-tab!")
            return
        
        if index < 0 or index >= len(self.sub_tabs):
            return
        
        # Xóa UI
        tab_data = self.sub_tabs[index]
        tab_data.ui_refs['frame'].destroy()
        tab_data.ui_refs['tab_btn_frame'].destroy()
        
        # Xóa khỏi list
        self.sub_tabs.pop(index)
        self.subtab_frames.pop(index)
        
        # Cập nhật lại index cho các tab sau
        for i, tab in enumerate(self.sub_tabs):
            tab.name = f"Nội dung {i + 1}"
            # Cập nhật text nút
            for widget in tab.ui_refs['tab_btn_frame'].winfo_children():
                if isinstance(widget, ctk.CTkButton) and widget.cget("text") != "×":
                    widget.configure(text=tab.name, command=lambda idx=i: self.switch_to_subtab(idx))
        
        # Chuyển về tab đầu
        self.switch_to_subtab(0)
        self._update_progress()
    
    def save_current_tab_data(self):
        """Lưu data từ UI vào object"""
        if self.current_subtab_index < 0 or self.current_subtab_index >= len(self.sub_tabs):
            return
        
        tab = self.sub_tabs[self.current_subtab_index]
        tab.content = tab.ui_refs['txt_content'].get("1.0", "end").strip()
        tab.links = tab.ui_refs['txt_links'].get("1.0", "end").strip()
        # images đã được cập nhật trực tiếp qua methods
    
    def select_images_for_tab(self, tab_index):
        """Chọn ảnh cho sub-tab cụ thể"""
        if tab_index < 0 or tab_index >= len(self.sub_tabs):
            return
        
        tab_name = self.sub_tabs[tab_index].name
        
        files = filedialog.askopenfilenames(
            title=f"Chọn ảnh cho {tab_name}",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.webp *.bmp"), ("All files", "*.*")],
            initialdir=str(Path.home() / "Pictures")
        )
        if files:
            self.sub_tabs[tab_index].images.extend(files)
            self._update_image_label(tab_index)
            self._show_status(f"{tab_name}: Đã chọn {len(files)} ảnh")
    
    def clear_images_for_tab(self, tab_index):
        """Xóa ảnh cho sub-tab"""
        self.sub_tabs[tab_index].images = []
        self._update_image_label(tab_index)
        self._show_status(f"{self.sub_tabs[tab_index].name}: Đã xóa ảnh")
    
    def paste_images_for_tab(self, tab_index):
        """Paste ảnh từ clipboard cho sub-tab"""
        if not CLIPBOARD_SUPPORT:
            return
        
        try:
            import tempfile
            
            # Thử lấy file paths
            win32clipboard.OpenClipboard()
            try:
                data = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                win32clipboard.CloseClipboard()
                image_files = [f for f in data if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'))]
                if image_files:
                    self.sub_tabs[tab_index].images.extend(image_files)
                    self._update_image_label(tab_index)
                    self._show_status(f"Đã dán {len(image_files)} ảnh từ clipboard")
                    return
            except:
                win32clipboard.CloseClipboard()
            
            # Thử lấy bitmap
            try:
                img = ImageGrab.grabclipboard()
                if hasattr(img, 'save'):
                    temp_path = os.path.join(tempfile.gettempdir(), f"pasted_{datetime.now().strftime('%H%M%S')}.png")
                    img.save(temp_path, "PNG")
                    self.sub_tabs[tab_index].images.append(temp_path)
                    self._update_image_label(tab_index)
                    self._show_status("Đã dán ảnh từ clipboard")
            except:
                pass
        except Exception as e:
            self._show_status(f"Lỗi paste: {str(e)[:50]}")
    
    def _update_image_label(self, tab_index):
        """Cập nhật label ảnh"""
        tab = self.sub_tabs[tab_index]
        lbl = tab.ui_refs['lbl_images']
        
        if tab.images:
            count = len(tab.images)
            names = ", ".join([Path(f).name for f in tab.images[:2]])
            if count > 2:
                names += f" +{count-2}"
            lbl.configure(text=f"📷 {count} ảnh: {names}", text_color="#28a745")
        else:
            lbl.configure(text="📷 Chưa chọn ảnh", text_color="gray")
    
    def _update_progress(self):
        """Cập nhật progress label"""
        total = len(self.sub_tabs)
        completed = sum(1 for t in self.sub_tabs if t.is_completed)
        self.lbl_progress.configure(text=f"{total} sub-tabs | {completed} hoàn thành")
    
    def _show_status(self, message):
        """Hiển thị status"""
        self.lbl_status.configure(text=message)
    
    def run_all_subtabs(self):
        """Chạy tuần tự tất cả sub-tabs"""
        if self.is_running:
            self.is_running = False
            self.btn_run_all.configure(text="🚀 CHẠY TẤT CẢ SUB-TABS", fg_color="#dc3545")
            return
        
        # Lưu data hiện tại
        self.save_current_tab_data()
        
        # Kiểm tra có sub-tab nào có data không
        valid_tabs = []
        for i, tab in enumerate(self.sub_tabs):
            if tab.content and tab.links:
                valid_tabs.append(i)
        
        if not valid_tabs:
            self._show_status("Không có sub-tab nào có đủ nội dung và link!")
            return
        
        self.is_running = True
        self.btn_run_all.configure(text="🛑 DỪNG", fg_color="#6c757d")
        
        # Reset trạng thái
        for tab in self.sub_tabs:
            tab.is_completed = False
            tab.ui_refs['lbl_status'].configure(text="⏳ Chờ...", text_color="gray")
        
        # Chạy trong thread
        threading.Thread(target=self._run_campaign, args=(valid_tabs,), daemon=True).start()
    
    def _run_campaign(self, tab_indices):
        """Campaign runner - chạy tuần tự các sub-tabs"""
        is_spin = self.sw_spin.get()
        total_tabs = len(tab_indices)
        
        for idx, tab_idx in enumerate(tab_indices):
            if not self.is_running:
                self.after(0, lambda: self._show_status("Đã dừng chiến dịch"))
                break
            
            tab = self.sub_tabs[tab_idx]
            
            # Log chuyển tab
            print(f"\n{'='*50}")
            print(f"[CAMPAIGN] Chuyển sang {tab.name} ({idx+1}/{total_tabs})")
            print(f"{'='*50}")
            
            # Highlight tab đang chạy - capture giá trị đúng
            current_tab_idx = tab_idx
            current_tab = tab
            current_idx = idx + 1
            
            self.after(0, lambda i=current_tab_idx: self.switch_to_subtab(i))
            self.after(0, lambda t=current_tab, c=f"🔄 Đang chạy ({current_idx}/{total_tabs})...": 
                        t.ui_refs['lbl_status'].configure(text=c, text_color="#1877F2"))
            self.after(0, lambda n=current_tab.name, i=current_idx, t=total_tabs: 
                        self._show_status(f"▶ Đang chạy {n} ({i}/{t})"))
            
            # Parse links
            links = [l.strip() for l in tab.links.split('\n') if l.strip()]
            total_links = len(links)
            
            print(f"[CAMPAIGN] {tab.name} có {total_links} link cần đăng")
            
            # Chạy từng link
            for link_idx, link in enumerate(links):
                if not self.is_running:
                    print("[CAMPAIGN] Đã dừng chiến dịch")
                    break
                
                progress = f"[{link_idx+1}/{total_links}]"
                print(f"[CAMPAIGN] {tab.name} {progress} Đang đăng: {link[:60]}...")
                
                current_link = link
                current_tab_name = tab.name
                current_progress = progress
                
                self.after(0, lambda l=current_link, n=current_tab_name, p=current_progress: 
                            self.add_log(l, f"{n} {p} Đang đăng..."))
                
                success, msg = self.bot.post_to_target(link, tab.content, is_spin, tab.images)
                
                result_msg = msg
                print(f"[CAMPAIGN] {current_tab_name} {current_progress} Kết quả: {result_msg}")
                self.after(0, lambda l=current_link, m=result_msg: self.add_log(l, m))
                
                # Delay giữa các link
                if self.is_running and link_idx < len(links) - 1:
                    delay = random.randint(30, 60)
                    print(f"[CAMPAIGN] Nghỉ {delay}s trước link tiếp theo...")
                    self.after(0, lambda d=delay: self._show_status(f"⏸ Nghỉ {d}s..."))
                    time.sleep(delay)
            
            # Mark completed
            tab.is_completed = True
            print(f"[CAMPAIGN] ✅ {tab.name} HOÀN THÀNH")
            
            # Delay giữa các tab (trừ tab cuối)
            if self.is_running and idx < len(tab_indices) - 1:
                delay = random.randint(15, 30)
                print(f"[CAMPAIGN] Nghỉ {delay}s trước khi sang tab tiếp theo...")
                self.after(0, lambda d=delay: self._show_status(f"⏸ Chuyển tab sau {d}s..."))
                time.sleep(delay)
            
            completed_tab = tab
            self.after(0, lambda t=completed_tab: t.ui_refs['lbl_status'].configure(
                text="✅ Hoàn thành", text_color="#28a745"))
            self.after(0, self._update_progress)
        
        # Done
        self.is_running = False
        self.after(0, lambda: self.btn_run_all.configure(
            text="🚀 CHẠY TẤT CẢ SUB-TABS", fg_color="#dc3545"))
        self.after(0, lambda: self._show_status("Hoàn thành tất cả sub-tabs!"))
    
    def open_chrome(self):
        """Mở Chrome cho instance này"""
        self.btn_browser.configure(state="disabled", text="⏳ Đang mở...")
        
        def _open():
            msg = self.bot.open_for_login()
            self.after(0, lambda: self._show_status(msg))
            self.after(0, lambda: self.btn_browser.configure(state="normal", text="▶ MỞ CHROME"))
        
        threading.Thread(target=_open, daemon=True).start()
    
    def add_log(self, target, message):
        """Log to console/status"""
        time_str = datetime.now().strftime("%H:%M:%S")
        print(f"[{time_str}] {target}: {message}")
        self._show_status(f"[{time_str}] {message[:60]}")
    
    def _get_save_file_path(self):
        """Trả về đường dẫn file lưu data cho instance này"""
        save_dir = Path(__file__).parent / "saved_data"
        save_dir.mkdir(exist_ok=True)
        return save_dir / f"instance_{self.instance_id}_data.json"
    
    def save_data(self):
        """Lưu tất cả sub-tabs vào file JSON"""
        try:
            # Lưu data hiện tại trước
            self.save_current_tab_data()
            
            # Chuẩn bị data để lưu
            data = {
                "instance_id": self.instance_id,
                "saved_at": datetime.now().isoformat(),
                "tabs": []
            }
            
            for tab in self.sub_tabs:
                tab_data = {
                    "name": tab.name,
                    "content": tab.content,
                    "links": tab.links,
                    "images": tab.images,  # Lưu cả đường dẫn ảnh
                    "is_completed": tab.is_completed
                }
                data["tabs"].append(tab_data)
            
            # Lưu vào file
            save_path = self._get_save_file_path()
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"[SAVE] Đã lưu {len(self.sub_tabs)} sub-tabs vào {save_path}")
            return True
        except Exception as e:
            print(f"[SAVE] Lỗi khi lưu: {e}")
            return False
    
    def _load_data_async(self):
        """Load data sau khi UI đã ready"""
        print("[INIT] Đang kiểm tra data đã lưu...")
        self.load_data()
    
    def load_data(self):
        """Load sub-tabs từ file JSON"""
        try:
            save_path = self._get_save_file_path()
            if not save_path.exists():
                print(f"[LOAD] Không tìm thấy file lưu cho instance {self.instance_id}")
                return False
            
            with open(save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Xóa tab mặc định đã tạo nếu nó trống
            if len(self.sub_tabs) == 1:
                first_tab = self.sub_tabs[0]
                if not first_tab.content and not first_tab.links and not first_tab.images:
                    print("[LOAD] Xóa tab mặc định trống")
                    self.remove_sub_tab(0)
            
            # Tạo các tab từ data đã lưu
            loaded_count = 0
            for tab_data in data.get("tabs", []):
                self.add_sub_tab_with_data(
                    name=tab_data.get("name", f"Nội dung {loaded_count+1}"),
                    content=tab_data.get("content", ""),
                    links=tab_data.get("links", ""),
                    images=tab_data.get("images", [])
                )
                loaded_count += 1
            
            # Chuyển về tab đầu tiên
            if self.sub_tabs:
                self.switch_to_subtab(0)
            
            print(f"[LOAD] ✅ Đã khôi phục {loaded_count} sub-tabs từ {save_path}")
            self._show_status(f"✅ Đã khôi phục {loaded_count} sub-tabs")
            return True
        except Exception as e:
            print(f"[LOAD] ❌ Lỗi khi load: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def add_sub_tab_with_data(self, name, content, links, images):
        """Thêm sub-tab với data đã có (dùng khi load)"""
        idx = len(self.sub_tabs)
        
        # Tạo data
        tab_data = SubTabData(name)
        tab_data.content = content
        tab_data.links = links
        tab_data.images = images
        self.sub_tabs.append(tab_data)
        
        # (Phần tạo UI tương tự add_sub_tab nhưng không cần switch)
        # ... tạo UI như bình thường ...
        tab_btn_frame = ctk.CTkFrame(self.tab_bar, fg_color="#e0e0e0", corner_radius=8, width=120, height=32)
        tab_btn_frame.pack(side="left", padx=2, pady=3)
        tab_btn_frame.pack_propagate(False)
        
        btn_switch = ctk.CTkButton(tab_btn_frame, text=name, width=80, height=28,
                                  font=("Arial", 11), fg_color="transparent", hover_color="#d0d0d0",
                                  text_color="black", command=lambda i=idx: self.switch_to_subtab(i))
        btn_switch.pack(side="left", padx=2)
        
        if len(self.sub_tabs) > 1:
            btn_close = ctk.CTkButton(tab_btn_frame, text="×", width=24, height=28,
                                     font=("Arial", 12, "bold"), fg_color="transparent",
                                     hover_color="#ff6b6b", text_color="#666",
                                     command=lambda i=idx: self.remove_sub_tab(i))
            btn_close.pack(side="right", padx=2)
        
        # Tạo frame và UI (simplified)
        frame = ctk.CTkFrame(self.tab_container, fg_color="white")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=0)
        
        # Content frame (left)
        content_frame = ctk.CTkFrame(frame, fg_color="white", corner_radius=10, border_width=2, border_color="#dee2e6")
        content_frame.grid(row=0, column=0, padx=(15, 8), pady=15, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=0)
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_rowconfigure(2, weight=0)
        
        ctk.CTkLabel(content_frame, text="📝 NỘI DUNG BÀI VIẾT", 
                    font=("Arial", 14, "bold"), text_color="#1877F2").grid(row=0, column=0, sticky="w", padx=15, pady=(12, 8))
        
        txt_content = ctk.CTkTextbox(content_frame, height=200, border_width=1, font=("Arial", 12))
        txt_content.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        txt_content.insert("1.0", content)
        
        tooltip = "💡 Ctrl+Click: chọn ảnh | Ctrl+Shift+V: dán ảnh" if CLIPBOARD_SUPPORT else "💡 Ctrl+Click: chọn ảnh"
        ctk.CTkLabel(content_frame, text=tooltip, font=("Arial", 10), text_color="gray").grid(row=2, column=0, sticky="e", padx=15, pady=(0, 10))
        
        txt_content.bind("<Control-Button-1>", lambda e, t=idx: self.select_images_for_tab(t))
        if CLIPBOARD_SUPPORT:
            txt_content.bind("<Control-Shift-KeyPress-v>", lambda e, t=idx: self.paste_images_for_tab(t))
        
        # Links frame (right)
        links_frame = ctk.CTkFrame(frame, fg_color="white", corner_radius=10, border_width=2, border_color="#dee2e6")
        links_frame.grid(row=0, column=1, padx=(8, 15), pady=15, sticky="nsew")
        links_frame.grid_columnconfigure(0, weight=1)
        links_frame.grid_rowconfigure(0, weight=0)
        links_frame.grid_rowconfigure(1, weight=0)
        links_frame.grid_rowconfigure(2, weight=1)
        links_frame.grid_rowconfigure(3, weight=0)
        
        ctk.CTkLabel(links_frame, text="🔗 LINK NHÓM FACEBOOK", 
                    font=("Arial", 14, "bold"), text_color="#dc3545").grid(row=0, column=0, sticky="w", padx=15, pady=(12, 5))
        
        ctk.CTkLabel(links_frame, text="Mỗi dòng 1 link", 
                    font=("Arial", 11), text_color="gray").grid(row=1, column=0, sticky="w", padx=15, pady=(0, 5))
        
        txt_links = ctk.CTkTextbox(links_frame, height=200, border_width=1, font=("Arial", 11))
        txt_links.grid(row=2, column=0, sticky="nsew", padx=15, pady=5)
        txt_links.insert("1.0", links)
        
        status_frame = ctk.CTkFrame(links_frame, fg_color="#f8f9fa", corner_radius=5, height=40)
        status_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(8, 12))
        status_frame.grid_columnconfigure(0, weight=1)
        
        lbl_status = ctk.CTkLabel(status_frame, text="⏳ Chưa chạy", 
                                 font=("Arial", 12), text_color="#6c757d")
        lbl_status.grid(row=0, column=0, sticky="w", padx=10, pady=8)
        
        # Images frame (bottom)
        images_frame = ctk.CTkFrame(frame, fg_color="#f8f9fa", corner_radius=10, border_width=2, border_color="#dee2e6")
        images_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        
        ctk.CTkLabel(images_frame, text="📷 ẢNH ĐÍNH KÈM", 
                    font=("Arial", 14, "bold"), text_color="#28a745").pack(anchor="w", padx=15, pady=(12, 8))
        
        # Hiển thị số ảnh đã load
        if images:
            count = len(images)
            names = ", ".join([Path(f).name for f in images[:2]])
            if count > 2:
                names += f" +{count-2}"
            img_text = f"📷 {count} ảnh: {names}"
            img_color = "#28a745"
        else:
            img_text = "Chưa chọn ảnh nào"
            img_color = "#6c757d"
        
        lbl_images = ctk.CTkLabel(images_frame, text=img_text, text_color=img_color, font=("Arial", 12))
        lbl_images.pack(anchor="w", padx=15, pady=(3, 10))
        
        img_btn_frame = ctk.CTkFrame(images_frame, fg_color="transparent")
        img_btn_frame.pack(fill="x", padx=15, pady=(3, 15))
        
        def make_select_handler(tab_idx):
            return lambda: self.select_images_for_tab(tab_idx)
        
        def make_clear_handler(tab_idx):
            return lambda: self.clear_images_for_tab(tab_idx)
        
        btn_select = ctk.CTkButton(img_btn_frame, text="📎 CHỌN ẢNH", width=140, height=40,
                                  command=make_select_handler(idx),
                                  fg_color="#1877F2", hover_color="#166fe5",
                                  font=("Arial", 13, "bold"), corner_radius=8)
        btn_select.pack(side="left", padx=(0, 15), pady=5)
        
        btn_clear = ctk.CTkButton(img_btn_frame, text="🗑️ XÓA", width=100, height=40,
                                 command=make_clear_handler(idx),
                                 fg_color="#dc3545", hover_color="#c82333",
                                 font=("Arial", 13), corner_radius=8)
        btn_clear.pack(side="left", pady=5)
        
        # Lưu refs
        tab_data.ui_refs = {
            'frame': frame,
            'tab_btn_frame': tab_btn_frame,
            'txt_content': txt_content,
            'txt_links': txt_links,
            'lbl_images': lbl_images,
            'lbl_status': lbl_status,
            'btn_switch': btn_switch
        }
        
        self.subtab_frames.append(frame)
        self._update_progress()
        return idx
    
    def _on_closing(self):
        """Cleanup khi đóng - tự động lưu data"""
        print("[EXIT] Đang lưu data trước khi đóng...")
        self.save_data()
        self.is_running = False
        self.bot.quit()
        self.destroy()


if __name__ == "__main__":
    instance_id = 1
    if len(sys.argv) > 1:
        try:
            instance_id = int(sys.argv[1])
        except ValueError:
            pass
    
    app = ProfessionalGroupPost(instance_id=instance_id)
    app.mainloop()
