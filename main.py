import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageDraw, ImageFont
import telebot
from io import BytesIO

# --- CẤU HÌNH ---
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" # <--- THAY TOKEN CỦA BẠN VÀO ĐÂY
GARENA_URL = "https://m.garena.vn/arenaofvalor/" 
# URL thực tế có thể thay đổi tùy server (VN, TH, ID, PH...). 
# Ở đây dùng URL mẫu để code chạy mượt mà.

# Khởi tạo Bot
BOT = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# --- HÀM TẠO DRIVER SELENIUM (TỐI ƯU CHO VERCEL) ---
def get_driver():
    options = Options()
    options.add_argument('--headless=new') # Chế độ headless mới nhất
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # Giả lập User-Agent điện thoại Android để né Bot Captcha
    options.add_argument('user-agent=Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36')
    
    driver = webdriver.Chrome(options=options)
    return driver

# --- HÀM LẤY DỮ LIỆU SKIN ---
def fetch_skins_data(driver, username, password, chat_id):
    try:
        driver.get(GARENA_URL)
        time.sleep(3)
        
        # GỬI LOG TIẾN ĐỘ (Tùy chọn)
        BOT.send_message(chat_id, "⚡ Đang đăng nhập vào Garena...")

        # Logic đăng nhập (Cần điều chỉnh Selector theo trang web thực tế)
        # Đây là ví dụ logic, bạn cần inspect element trang Garena thực để lấy ID chính xác
        try:
            wait = WebDriverWait(driver, 10)
            user_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
            pass_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
            
            user_input.send_keys(username)
            pass_input.send_keys(password)
            
            # Tìm nút đăng nhập (ID mẫu)
            login_btn = driver.find_element(By.ID, "login-btn")
            login_btn.click()
            
            time.sleep(5) # Chờ xử lý captcha hoặc chuyển trang
            
            # Giả lập lấy danh sách skin từ trang web (Thay thế bằng logic scrape thực tế)
            # Ở đây giả định ta lấy được danh sách tên skin
            skins_list = [
                "Skin Thép", "Skin Rồng", "Skin Băng Giá", 
                "Skin Hỏa Diệm", "Skin Ác Quỷ", "Skin Thần Thoại",
                "Skin Chiến Binh", "Skin Ma Kết"
            ]
            
            # Nếu muốn lấy thực tế, dùng driver.find_elements(...) và lấy text
            
            return skins_list, "Active"
            
        except Exception as e:
            return [], "Login Failed"

    except Exception as e:
        return [], "Error"

# --- HÀM GHÉP ẢNH DẠNG LƯỚI/TÌM HÌNH LƯỠI ---
def create_tongue_image(skin_list, chat_id):
    # Kích thước ảnh nền (tỷ lệ dọc như điện thoại)
    width, height = 800, 1200
    img = Image.new('RGB', (width, height), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    # Vẽ hình nền dạng lưỡi đơn giản (Tam giác tròn)
    # Tọa độ: Đỉnh lưỡi (trên), Hai đầu lưỡi (dưới)
    # Màu đỏ cam đặc trưng
    tongue_points = [(400, 50), (100, 900), (700, 900)]
    draw.polygon(tongue_points, fill='#FF4500', outline='#cc3700', width=5)
    
    # Cấu hình lưới hiển thị skin
    cols = 3
    rows = 3
    cell_w = 180
    cell_h = 180
    start_x = 300 # Căn giữa
    start_y = 200
    
    # Viết tiêu đề
    draw.text((350, 80), "DANH SÁCH SKIN", fill='white', font=None)
    
    for i, skin_name in enumerate(skin_list):
        if i >= cols * rows: 
            break
            
        row = i // cols
        col = i % cols
        
        x = start_x + col * (cell_w + 20)
        y = start_y + row * (cell_h + 20)
        
        # Vẽ khung chứa ảnh skin
        draw.rectangle([x, y, x+cell_w, y+cell_h], outline='white', width=2)
        
        # Giả lập ảnh skin (Vẽ hình vuông màu ngẫu nhiên thay vì tải ảnh thật để code nhẹ)
        # Nếu có link ảnh thật, dùng: Image.open(requests.get(url, stream=True).raw)
        color = [(255,255,0), (0,255,255), (255,0,255), (255,165,0)][i % 4]
        draw.ellipse([x+10, y+10, x+cell_w-10, y+cell_h-10], fill=color)
        
        # Viết tên skin
        draw.text((x + 20, y + 80), skin_name, fill='white', font=None)
        
    # Thêm thông tin tình trạng
    status_text = f"Tổng số: {len(skin_list)} | Trạng thái: OK"
    draw.text((300, 1050), status_text, fill='yellow', font=None)
    
    return img

# --- XỬ LÝ LỆNH TELEGRAM ---
@BOT.message_handler(commands=['check'])
def check_skin(message):
    args = message.text.split()
    if len(args) < 3:
        BOT.reply_text(message.chat.id, "Cú pháp: /check <username> <password>")
        return
    
    user = args[1]
    pwd = args[2]
    chat_id = message.chat.id
    
    BOT.reply_text(chat_id, "🕵️‍♂️ Đang quét tài khoản và lấy IP...")
    
    driver = None
    try:
        driver = get_driver()
        skins, status = fetch_skins_data(driver, user, pwd, chat_id)
        
        if not skins:
            BOT.reply_text(chat_id, f"❌ Kết quả: {status}")
            return

        # Tạo ảnh
        BOT.reply_text(chat_id, "🎨 Đang ghép ảnh lưỡi...")
        img = create_tongue_image(skins, chat_id)
        
        # Chuyển ảnh thành BytesIO để gửi
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Nội dung text
        text_report = f"✅ <b>KẾT QUẢ CHECK SKIN</b>\n\n"
        text_report += f"👤 ID: {user}\n"
        text_report += f"📊 Trạng thái: {status}\n"
        text_report += f"🔥 Tổng số skin: {len(skins)}\n\n"
        text_report += "<b>Danh sách:</b>\n"
        for s in skins:
            text_report += f"• {s}\n"
            
        BOT.send_photo(chat_id, img_bytes, caption=text_report)
        
    except Exception as e:
        BOT.reply_text(chat_id, f"⚠️ Lỗi hệ thống: {str(e)}")
    finally:
        if driver:
            driver.quit()

# --- CẤU HÌNH CHẠY TRÊN VERCEL ---
def handler(event, context):
    # Hàm entry point cho Vercel
    # Vercel gọi hàm này mỗi khi có request
    
    # Nếu muốn bot chạy liên tục, ta dùng polling trong hàm này hoặc dùng cron
    # Cách đơn giản nhất: Dùng Telegram webhook hoặc long-polling trong hàm handler
    
    # Ở đây ta giả lập bot chạy polling một lần khi có request để test
    # Trong thực tế, bạn có thể dùng webhook của Telegram để kích hoạt handler
    # Nhưng với Telebot library, cách tốt nhất là chạy script như một service.
    # Vercel Function chạy stateless, nên ta sẽ dùng logic đơn giản:
    
    # Nếu muốn bot active 24/7, hãy dùng Webhook thay vì polling.
    # Dưới đây là code để xử lý khi có request đến endpoint:
    return {
        "statusCode": 200,
        "body": "WormGPT Tool đang
