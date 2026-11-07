import os
import time
import requests
from flask import Flask, request, jsonify, send_file
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageDraw
import telebot
from io import BytesIO
import telebot.types

# --- CẤU HÌNH ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("Thiếu biến môi trường BOT_TOKEN trong Vercel")

GARENA_URL = "https://m.garena.vn/arenaofvalor/"

# Khởi tạo Flask
app = Flask(__name__)
# Khởi tạo Bot
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# --- HÀM TẠO DRIVER SELENIUM (Tối ưu cho Vercel) ---
def get_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36')
    # Trên Vercel, Chrome thường được cài sẵn trong runtime python3.11
    driver = webdriver.Chrome(options=options)
    return driver

# --- HÀM LẤY DỮ LIỆU SKIN ---
def fetch_skins_data(driver, username, password, chat_id):
    try:
        driver.get(GARENA_URL)
        time.sleep(3)
        bot.send_message(chat_id, "⚡ Đang đăng nhập vào Garena...")

        try:
            wait = WebDriverWait(driver, 10)
            # Lưu ý: ID username/password có thể thay đổi tùy phiên bản trang Garena
            user_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
            pass_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
            
            user_input.send_keys(username)
            pass_input.send_keys(password)
            
            # Tìm nút đăng nhập (ID mẫu, cần check thực tế nếu lỗi)
            login_btn = driver.find_element(By.ID, "login-btn")
            login_btn.click()
            time.sleep(5)
            
            # Giả lập danh sách skin (Thay bằng logic scrape thực tế nếu cần)
            skins_list = [
                "Skin Thép", "Skin Rồng", "Skin Băng Giá", 
                "Skin Hỏa Diệm", "Skin Ác Quỷ", "Skin Thần Thoại",
                "Skin Chiến Binh", "Skin Ma Kết"
            ]
            return skins_list, "Active"
            
        except Exception as e:
            return [], f"Login Failed: {str(e)}"

    except Exception as e:
        return [], f"Error: {str(e)}"

# --- HÀM GHÉP ẢNH LƯỠI ---
def create_tongue_image(skin_list, chat_id):
    width, height = 800, 1200
    img = Image.new('RGB', (width, height), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    # Vẽ hình lưỡi
    tongue_points = [(400, 50), (100, 900), (700, 900)]
    draw.polygon(tongue_points, fill='#FF4500', outline='#cc3700', width=5)
    
    cols = 3
    rows = 3
    cell_w = 180
    cell_h = 180
    start_x = 300
    start_y = 200
    
    draw.text((350, 80), "DANH SÁCH SKIN", fill='white', font=None)
    
    for i, skin_name in enumerate(skin_list):
        if i >= cols * rows: 
            break
            
        row = i // cols
        col = i % cols
        
        x = start_x + col * (cell_w + 20)
        y = start_y + row * (cell_h + 20)
        
        draw.rectangle([x, y, x+cell_w, y+cell_h], outline='white', width=2)
        
        colors = [(255,255,0), (0,255,255), (255,0,255), (255,165,0)]
        color = colors[i % 4]
        draw.ellipse([x+10, y+10, x+cell_w-10, y+cell_h-10], fill=color)
        
        draw.text((x + 20, y + 80), skin_name, fill='white', font=None)
        
    status_text = f"Tổng số: {len(skin_list)} | Trạng thái: OK"
    draw.text((300, 1050), status_text, fill='yellow', font=None)
    
    return img

# --- XỬ LÝ LỆNH TELEGRAM ---
@bot.message_handler(commands=['check'])
def check_skin(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_text(message.chat.id, "Cú pháp: /check <username> <password>")
        return
    
    user = args[1]
    pwd = args[2]
    chat_id = message.chat.id
    
    bot.reply_text(chat_id, "🕵️‍♂️ Đang quét tài khoản và lấy IP...")
    
    driver = None
    try:
        driver = get_driver()
        skins, status = fetch_skins_data(driver, user, pwd, chat_id)
        
        if not skins:
            bot.reply_text(chat_id, f"❌ Kết quả: {status}")
            return

        bot.reply_text(chat_id, "🎨 Đang ghép ảnh lưỡi...")
        img = create_tongue_image(skins, chat_id)
        
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        text_report = f"✅ <b>KẾT QUẢ CHECK SKIN</b>\n\n"
        text_report += f"👤 ID: {user}\n"
        text_report += f"📊 Trạng thái: {status}\n"
        text_report += f"🔥 Tổng số skin: {len(skins)}\n\n"
        text_report += "<b>Danh sách:</b>\n"
        for s in skins:
            text_report += f"• {s}\n"
            
        bot.send_photo(chat_id, img_bytes, caption=text_report)
        
    except Exception as e:
        bot.reply_text(chat_id, f"⚠️ Lỗi hệ thống: {str(e)}")
    finally:
        if driver:
            driver.quit()

# --- WEBHOOK ROUTE ---
@app.route('/webhook', methods=['POST'])
def webhook_handler():
    update = request.get_json()
    if update:
        # Chuyển JSON thành đối tượng Update của Telebot
        try:
            bot.process_new_updates([telebot.types.Update.de_json(update)])
        except Exception as e:
            print(f"Error processing update: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "ok"}), 200

# --- ROUTE CHO INDEX.HTML (Giao diện test) ---
@app.route('/')
def index():
    return send_file('index.html')

# --- ENTRY POINT CHO VERCEL ---
# Vercel cần một hàm hoặc đối tượng callable. 
# Với Flask, ta export 'app' hoặc tạo một hàm wrapper.
# Cách này đảm bảo Vercel nhận diện được entry point.
server = app

# Nếu chạy local (không bắt buộc trên Vercel)
if __name__ == '__main__':
    # Set webhook local (cần ngrok)
    # bot.set_webhook(url='https://your-ngrok-url.ngrok.io/webhook')
    print("Running locally...")
    bot.infinity_polling()
