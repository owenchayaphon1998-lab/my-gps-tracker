import os
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import sqlite3
from database import get_connection

load_dotenv()
app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

def send_telegram_message(text):
    if not TELEGRAM_TOKEN or not GROUP_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        return response.ok
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check_customer', methods=['POST'])
def check_customer():
    data = request.json
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"success": False, "message": "กรุณากรอกชื่อ"})

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Check if scammer
    cursor.execute("SELECT description FROM scammer_database WHERE full_name LIKE ?", (f"%{name}%",))
    scammer = cursor.fetchone()
    if scammer:
        conn.close()
        return jsonify({
            "success": False, 
            "is_scammer": True, 
            "message": f"🚨 ตรวจพบประวัติมิจฉาชีพ: {scammer[0]}"
        })

    # 2. Check if duplicate customer
    cursor.execute("SELECT username, searched_at FROM search_history WHERE search_name = ? ORDER BY searched_at DESC LIMIT 1", (name,))
    history = cursor.fetchone()

    if history:
        conn.close()
        return jsonify({
            "success": False, 
            "is_duplicate": True, 
            "message": f"⚠️ ชื่อซ้ำ! เคยมีคนตรวจชื่อนี้แล้วเมื่อ {history[1]}"
        })

    # 3. Not duplicate, not scammer -> Save and notify group
    cursor.execute(
        "INSERT INTO search_history (user_id, username, search_name) VALUES (?, ?, ?)",
        ("WEB_DASHBOARD", "System", name)
    )
    conn.commit()
    conn.close()

    # Notify Telegram Group
    msg = f"✅ <b>บันทึกลูกค้าใหม่จากระบบเว็บ</b>\n👤 ชื่อ: {name}"
    send_telegram_message(msg)

    return jsonify({"success": True, "message": "✅ ไม่พบประวัติซ้ำ บันทึกชื่อและแจ้งเตือนเข้ากลุ่มเรียบร้อย!"})

@app.route('/api/add_scammer', methods=['POST'])
def add_scammer():
    data = request.json
    name = data.get('name', '').strip()
    bank = data.get('bank', '').strip()
    desc = data.get('desc', '').strip()

    if not name or not desc:
        return jsonify({"success": False, "message": "กรุณากรอกชื่อและพฤติกรรมให้ครบถ้วน"})

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scammer_database (full_name, bank_account, description, severity)
        VALUES (?, ?, ?, 'HIGH')
    ''', (name, bank, desc))
    conn.commit()
    conn.close()

    # Notify Group
    msg = f"🚨 <b>เพิ่มรายชื่อมิจฉาชีพใหม่จากหน้าเว็บ!</b>\n👤 ชื่อ: {name}\n🏦 บัญชี: {bank}\n📝 พฤติกรรม: {desc}"
    send_telegram_message(msg)

    return jsonify({"success": True, "message": "✅ บันทึกรายชื่อมิจฉาชีพเรียบร้อย"})

@app.route('/api/customers', methods=['GET'])
def get_customers():
    conn = get_connection()
    cursor = conn.cursor()
    # Using GROUP BY to get distinct names, keeping the max ID (most recent)
    cursor.execute("SELECT MAX(id), search_name, MAX(searched_at) FROM search_history GROUP BY search_name ORDER BY MAX(id) DESC")
    rows = cursor.fetchall()
    conn.close()
    
    customers = [{"id": r[0], "name": r[1], "date": r[2]} for r in rows]
    return jsonify({"success": True, "customers": customers})

@app.route('/api/delete_customer', methods=['POST'])
def delete_customer():
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({"success": False, "message": "Missing name"})
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM search_history WHERE search_name = ?", (name,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route('/api/scammers', methods=['GET'])
def get_scammers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, bank_account, description FROM scammer_database ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    scammers = [{"id": r[0], "name": r[1], "bank": r[2] or "-", "desc": r[3] or "-"} for r in rows]
    return jsonify({"success": True, "scammers": scammers})

@app.route('/api/delete_scammer', methods=['POST'])
def web_delete_scammer():
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({"success": False, "message": "Missing name"})
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scammer_database WHERE full_name = ?", (name,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted > 0:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "ไม่พบรายชื่อในระบบ"})

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
