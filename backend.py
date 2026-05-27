import json
import time
import random
import socket
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



def find_free_port(start=9222, max_port=9322):

    """Tìm port trống cho Chrome remote debugging"""

    for port in range(start, max_port):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

            if s.connect_ex(('localhost', port)) != 0:

                return port

    raise RuntimeError("Không tìm được port trống")




class FacebookBot:

    def __init__(self, instance_id=1):

        self.driver = None

        self.instance_id = instance_id

        self.debug_port = find_free_port(9222 + (instance_id - 1) * 10)

        self.profile_dir = Path(__file__).parent / f"chrome_profile_{instance_id}"

        self.profile_dir.mkdir(exist_ok=True)



    def open_for_login(self):

        # Fix #5: tránh mở nhiều instance

        if self.driver:

            try:

                _ = self.driver.title

                return "Trình duyệt đã mở sẵn rồi!"

            except Exception:

                self.driver = None



        try:

            # Xóa lock file nếu Chrome bị tắt đột ngột lần trước

            for lock_file in ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket", "DevToolsActivePort"]:

                lock_path = self.profile_dir / lock_file

                if lock_path.exists():

                    lock_path.unlink(missing_ok=True)



            # Reset crash state trong Local State nếu có

            local_state_path = self.profile_dir / "Local State"

            if local_state_path.exists():

                try:

                    state = json.loads(local_state_path.read_bytes().decode("utf-8-sig"))

                    state["variations_crash_streak"] = 0

                    stab = state.get("user_experience_metrics", {}).get("stability", {})

                    stab["exit_type"] = "Normal"

                    stab["exited_cleanly"] = True

                    local_state_path.write_text(

                        json.dumps(state, ensure_ascii=False, separators=(",", ":")),

                        encoding="utf-8"

                    )

                except Exception:

                    pass



            options = webdriver.ChromeOptions()

            options.add_argument(f"--user-data-dir={self.profile_dir}")

            options.add_argument("--profile-directory=Default")

            options.add_argument(f"--remote-debugging-port={self.debug_port}")

            options.add_argument("--disable-notifications")

            options.add_argument("--start-maximized")

            options.add_argument("--no-sandbox")

            options.add_argument("--disable-dev-shm-usage")

            options.add_argument("--no-first-run")

            options.add_experimental_option("excludeSwitches", ["enable-automation"])

            options.add_experimental_option("useAutomationExtension", False)

            # Dùng webdriver-manager để tự tải chromedriver
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())

            print(f"[Tab {self.instance_id}] Starting Chrome with port {self.debug_port}...")

            self.driver = webdriver.Chrome(service=service, options=options)

            print(f"[Tab {self.instance_id}] Chrome started, navigating to Facebook...")

            self.driver.get("https://www.facebook.com")

            print(f"[Tab {self.instance_id}] Facebook loaded: {self.driver.title[:50]}")

            return f"Trình duyệt Tab {self.instance_id} đã mở. Hãy đăng nhập!"

        except Exception as e:

            print(f"[Tab {self.instance_id}] FAILED to start Chrome: {str(e)[:300]}")

            return f"Lỗi khởi động trình duyệt Tab {self.instance_id}: {str(e)[:150]}"



    def quit(self):

        if self.driver:

            try:

                self.driver.quit()

            except Exception:

                pass

            finally:

                self.driver = None



    def post_to_target(self, url, content, is_spin, image_paths=None):

        try:

            image_paths = image_paths or []

            if not self.driver:

                return False, "Lỗi: Chưa mở trình duyệt!"



            # Fix #6: kiểm tra session còn sống không

            try:

                title = self.driver.title

                print(f"[Tab {self.instance_id}] Session alive: {title[:50]}")

            except Exception as e:

                print(f"[Tab {self.instance_id}] Session dead: {e}")

                self.driver = None

                return False, "Lỗi: Trình duyệt đã bị đóng. Hãy mở lại!"

           

            print(f"[Tab {self.instance_id}] Navigating to: {url}")

            self.driver.get(url)

            wait = WebDriverWait(self.driver, 20)  # Tăng timeout

            time.sleep(random.randint(3, 5))  # Giảm sleep chờ trang load



            # Dọn dẹp các popup linh tinh trước khi làm

            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)



            # --- BƯỚC 1: CLICK NÚT MỞ Ô ĐĂNG ---

            print(f"[Tab {self.instance_id}] Finding post trigger button...")

            trigger_xpaths = [
                "//div[@role='button']//span[contains(text(), 'Bạn viết gì đi')]",
                "//div[@role='button']//span[contains(text(), 'viết gì')]",
                "//div[@role='main']//div[@role='button'][contains(., 'Bạn viết gì đi') or contains(., 'Bạn đang nghĩ gì')]",
                "//div[@role='main']//span[contains(text(), 'Bạn viết gì đi') or contains(text(), 'Bạn đang nghĩ gì')]",
                "//div[@role='main']//div[@aria-label='Tạo bài viết' or @aria-label='Create a post']",
                "//div[@role='main']//div[@data-pagelet='GroupInlineComposer']//div[@role='button']",
                "//form//div[@role='button'][contains(., 'viết')]",
                "//div[contains(@class, 'composer')]//div[@role='button']",
                "//div[contains(@class, 'x1lk') or contains(@class, 'x1y1')]//div[@role='button']",
            ]

            btn_open = None

            for i, xpath in enumerate(trigger_xpaths):

                try:

                    btn_open = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

                    print(f"[Tab {self.instance_id}] Found trigger with xpath {i+1}")

                    break

                except:

                    continue

            

            if not btn_open:
                # Thử click trực tiếp vào input composer mà không cần mở dialog
                try:
                    direct_input = self.driver.find_element(By.XPATH, "//div[@role='main']//div[@contenteditable='true']")
                    print(f"[Tab {self.instance_id}] Found direct input, clicking...")
                    self.driver.execute_script("arguments[0].click();", direct_input)
                    time.sleep(2)
                    content_input = direct_input
                    skip_dialog = True
                except:
                    return False, "Lỗi: Không tìm thấy nút mở hộp đăng bài. Facebook có thể đã thay đổi giao diện."
            else:
                self.driver.execute_script("arguments[0].click();", btn_open)
                print(f"[Tab {self.instance_id}] Clicked trigger button")
                time.sleep(3)  # Chờ dialog mở
                skip_dialog = False



            # --- BƯỚC 2: ĐIỀN NỘI DUNG TRƯỚC (QUAN TRỌNG) ---
            
            if not skip_dialog:
                print(f"[Tab {self.instance_id}] Finding content input in dialog...")
                time.sleep(2)
                
                dialog_input_xpaths = [
                    "//div[@role='dialog']//div[@role='textbox']",
                    "//div[@role='dialog']//textarea",
                    "//div[@role='dialog']//div[@contenteditable='true']",
                    "//form//div[@contenteditable='true']",
                ]
                
                content_input = None
                for i, xpath in enumerate(dialog_input_xpaths):
                    try:
                        content_input = wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
                        print(f"[Tab {self.instance_id}] Found content input with xpath {i+1}")
                        break
                    except:
                        continue
                
                if not content_input:
                    return False, "Lỗi: Không tìm thấy ô nhập nội dung trong dialog"
            else:
                print(f"[Tab {self.instance_id}] Using direct input (already found)")

           

            final_text = content

            if is_spin:

                final_text = f"{content}\n\n[ID: {random.randint(1000, 9999)}]"



            # Nhập liệu vào đúng ô trong Dialog

            print(f"[Tab {self.instance_id}] Typing content...")

            content_input.click()

            time.sleep(1)

            # Xóa nội dung cũ

            self.driver.execute_script(

                "arguments[0].focus();"

                "document.execCommand('selectAll', false, null);"

                "document.execCommand('delete', false, null);",

                content_input

            )

            time.sleep(0.5)

            # Cách 1: Thử dùng send_keys (tốt cho ASCII)

            try:

                content_input.send_keys(final_text)

                print(f"[Tab {self.instance_id}] Content sent via send_keys")

            except Exception as type_err:

                print(f"[Tab {self.instance_id}] send_keys failed: {type_err}, trying JS...")

                # Cách 2: Dùng JavaScript (fallback cho Unicode)

                self.driver.execute_script(

                    "var el = arguments[0];"

                    "var text = arguments[1];"

                    "el.focus();"

                    "for (var i = 0; i < text.length; i++) {"

                    "  var char = text.charAt(i);"

                    "  var before = el.innerHTML;"

                    "  if (char === '\n') {"

                    "    document.execCommand('insertHTML', false, '<br>');"

                    "  } else {"

                    "    document.execCommand('insertText', false, char);"

                    "  }"

                    "}"

                    "el.dispatchEvent(new Event('input', { bubbles: true }));",

                    content_input,

                    final_text

                )

                print(f"[Tab {self.instance_id}] Content sent via JS execCommand")

            

            # Verify content was entered

            entered_text = self.driver.execute_script("return arguments[0].innerText || arguments[0].textContent || '';", content_input)

            print(f"[Tab {self.instance_id}] Content in box: '{entered_text[:50]}...'")

            time.sleep(3)



            # --- BƯỚC 3: UPLOAD ẢNH NẾU CÓ (SAU NỘI DUNG) ---

            if image_paths:

                print(f"[Tab {self.instance_id}] Uploading {len(image_paths)} images...")

                try:

                    # Tìm và click nút Ảnh/Video trong dialog để mở file input

                    photo_btn = None

                    try:

                        photo_btn = self.driver.find_element(

                            By.XPATH,

                            "//div[@role='dialog']//div[@role='button'][contains(., 'Ảnh') or contains(., 'Photo') or contains(., 'Video')]"

                        )

                        photo_btn.click()

                        print(f"[Tab {self.instance_id}] Clicked Photo/Video button")

                        time.sleep(2)

                    except:

                        print(f"[Tab {self.instance_id}] No Photo/Video button found, trying direct file input...")

                    

                    # Tìm input file

                    file_input = None

                    try:

                        file_input = self.driver.find_element(By.XPATH, "//div[@role='dialog']//input[@type='file']")

                    except:

                        try:

                            file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")

                        except:

                            pass

                    

                    if not file_input:

                        return False, "Lỗi: Không tìm thấy input upload ảnh"

                    

                    # Gửi danh sách ảnh

                    files_str = '\n'.join(image_paths)

                    file_input.send_keys(files_str)

                    print(f"[Tab {self.instance_id}] Sent {len(image_paths)} image paths")

                    time.sleep(2)

                    

                    # Chờ ảnh upload và preview xuất hiện

                    WebDriverWait(self.driver, 30).until(

                        EC.presence_of_element_located((

                            By.XPATH,

                            "//div[@role='dialog']//img[contains(@src, 'facebook')] | "

                            "//div[@role='dialog']//div[contains(@style, 'background-image')] | "

                            "//div[@role='dialog']//div[@role='progressbar']"

                        ))

                    )

                    print(f"[Tab {self.instance_id}] Images uploaded and preview visible")

                    time.sleep(3)

                except Exception as img_err:

                    print(f"[Tab {self.instance_id}] Image upload error: {img_err}")

                    return False, f"Lỗi upload ảnh: {str(img_err).split(chr(10))[0][:100]}"

            

            time.sleep(2)



            # --- BƯỚC 4: BẤM NÚT ĐĂNG (TRONG DIALOG) ---

            print(f"[Tab {self.instance_id}] Finding post button...")

            # Chỉ tìm nút Đăng nằm trong thẻ role='dialog' với nhiều variant

            post_btn_xpaths = [

                "//div[@role='dialog']//div[@aria-label='Đăng']",

                "//div[@role='dialog']//span[text()='Đăng']",

                "//div[@role='dialog']//div[@aria-label='Post']",

                "//div[@role='dialog']//span[text()='Post']",

                "//div[@role='dialog']//button[contains(., 'Đăng') or contains(., 'Post')]",

                "//div[@role='dialog']//div[@role='button'][contains(., 'Đăng') or contains(., 'Post')]",

            ]

            

            btn_post = None

            for i, xpath in enumerate(post_btn_xpaths):

                try:

                    btn_post = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

                    print(f"[Tab {self.instance_id}] Found post button with xpath {i+1}")

                    break

                except:

                    continue

            

            if not btn_post:

                # Thử tìm nút có background màu xanh (thường là nút primary)

                try:

                    # Tìm tất cả các nút trong dialog và lấy cái cuối cùng (thường là nút Đăng)

                    buttons = self.driver.find_elements(By.XPATH, "//div[@role='dialog']//div[@role='button']")

                    if buttons:

                        btn_post = buttons[-1]  # Nút cuối thường là Đăng

                        print(f"[Tab {self.instance_id}] Using last button as post button")

                except:

                    return False, "Lỗi: Không tìm thấy nút Đăng trong dialog"

           

            # Dùng JS Click để không bị chặn

            btn_text = btn_post.text if hasattr(btn_post, 'text') else btn_post.get_attribute('aria-label') or 'Đăng'

            print(f"[Tab {self.instance_id}] Clicking post button: '{btn_text}'")

            self.driver.execute_script("arguments[0].click();", btn_post)

            print(f"[Tab {self.instance_id}] Clicked post button, waiting for submission...")

           

            # Chờ lâu một chút để bài đăng thực sự lên sóng

            time.sleep(12)

            # Kiểm tra xem dialog đã đóng chưa (bài đã đăng thành công)

            try:

                dialog_still_open = self.driver.find_element(By.XPATH, "//div[@role='dialog']//div[@role='textbox']")

                if dialog_still_open:

                    print(f"[Tab {self.instance_id}] Warning: Dialog still open, post may not have been submitted")

                    return False, "Lỗi: Dialog vẫn mở, bài chưa được đăng"

            except:

                print(f"[Tab {self.instance_id}] Post completed successfully")

                return True, "Thành công: Bài viết đã đăng!"



        except Exception as e:

            print(f"[Tab {self.instance_id}] EXCEPTION: {str(e)[:200]}")

            # Nếu lỗi, nhấn ESC để lần sau không bị kẹt cái Dialog cũ

            try: self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)

            except: pass

            lines = str(e).split('\n')

            err_msg = ' | '.join(l.strip() for l in lines[:2] if l.strip())

            return False, f"Lỗi: {err_msg}"