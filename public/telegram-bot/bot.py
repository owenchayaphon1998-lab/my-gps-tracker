import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
from database import get_connection, setup_database

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_admin(user_id: str, username: str) -> bool:
    if ADMIN_ID and user_id == ADMIN_ID:
        return True
        
    if not username:
        return False
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE username = ?", (username.lower(),))
    is_adm = cursor.fetchone() is not None
    conn.close()
    return is_adm

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"สวัสดี {user.mention_html()}! ผมคือบอทผู้ช่วยตรวจสอบรายชื่อ\n\n"
        "พิมพ์ชื่อ-นามสกุล หรือส่งข้อความที่มีรายชื่อมาให้ผม เพื่อทำการ:\n"
        "1. เช็คว่ามีเพื่อนในทีมเคยค้นหาชื่อนี้ไปแล้วหรือยัง (ป้องกันงานซ้ำ)\n"
        "2. เช็คว่าเป็นมิจฉาชีพที่มีประวัติการโกงหรือไม่\n\n"
        "ลองพิมพ์ชื่อคนที่ต้องการตรวจสอบมาได้เลยครับ!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_html(
        "🛠️ <b>รวมคำสั่งทั้งหมด (พิมพ์เป็นข้อความได้เลย):</b>\n\n"
        "<b>คำสั่งทั่วไป:</b>\n"
        "• พิมพ์ชื่อ-นามสกุล : เพื่อตรวจสอบประวัติ\n"
        "• <code>คำสั่ง</code> : ดูรวมคำสั่งทั้งหมด\n"
        "• <code>Idm</code> : ดูไอดีของคุณ\n"
        "• <code>Idg</code> : ดูไอดีของกลุ่ม\n\n"
        "<b>คำสั่งแอดมิน:</b>\n"
        "• <code>รายชื่อ</code> : ดูรายชื่อลูกค้าทั้งหมด\n"
        "• <code>ลบชื่อ [เลข]</code> : ลบลูกค้าตามลำดับ (เช่น ลบชื่อ 1)\n"
        "• <code>รายชื่อมิจ</code> : ดูรายชื่อมิจฉาชีพ\n"
        "• <code>เพิ่มชื่อมิจ</code> : เพิ่มมิจฉาชีพ (พิมพ์ชื่อในบรรทัดถัดไป)\n"
        "• <code>ลบชื่อมิจ [ชื่อ]</code> : ลบรายชื่อมิจฉาชีพ (เช่น ลบชื่อมิจ สมชาย ใจร้าย)\n\n"
        "<b>คำสั่งแอดมินหลัก (Super Admin):</b>\n"
        "• <code>เพิ่มแอดมิน @username</code> : ตั้งแอดมินใหม่\n"
        "• <code>ลบแอดมิน @username</code> : ถอดแอดมินออก\n"
        "• <code>Admin</code> : ดูรายชื่อแอดมินทั้งหมด"
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /check command for group chats."""
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("กรุณาระบุชื่อที่ต้องการเช็ค เช่น /check สมชาย ใจดี")
        return
        
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    reply_msg = check_name_in_db(text, user_id, username)
    if reply_msg:
        await update.message.reply_html(reply_msg)

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get user's Telegram ID."""
    user_id = update.effective_user.id
    await update.message.reply_text(f"Telegram ID ของคุณคือ: {user_id}\n\nนำตัวเลขนี้ไปใส่ในไฟล์ .env ที่ช่อง ADMIN_ID= เพื่อตั้งค่าให้คุณเป็นแอดมินหลักครับ")

async def groupid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get the Chat ID of the current group."""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    if chat_type in ['group', 'supergroup']:
        await update.message.reply_text(f"ID ของกลุ่มนี้คือ: {chat_id}\nนำเลขนี้ (รวมเครื่องหมายลบ ถ้ามี) ไปตั้งค่าใน GROUP_CHAT_ID= ได้เลยครับ")
    else:
        await update.message.reply_text("คำสั่งนี้ใช้ได้เฉพาะในกลุ่มเท่านั้นครับ")

async def addscammer_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to add a new scammer."""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username
    if not is_admin(user_id, username):
        await update.message.reply_text("❌ คุณไม่มีสิทธิ์ใช้งานคำสั่งนี้ (เฉพาะแอดมินเท่านั้น)")
        return
        
    text = " ".join(context.args)
    parts = [p.strip() for p in text.split('|')]
    if len(parts) < 3:
        await update.message.reply_text("❌ รูปแบบไม่ถูกต้อง!\nวิธีใช้: /addscammer ชื่อ-นามสกุล | เลขบัญชี | พฤติกรรมการโกง")
        return
        
    name, bank, desc = parts[0], parts[1], parts[2]
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scammer_database (full_name, bank_account, description, severity)
        VALUES (?, ?, ?, ?)
    ''', (name, bank, desc, 'HIGH'))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ เพิ่มรายชื่อมิจฉาชีพ '{name}' ลงในฐานข้อมูลเรียบร้อยแล้วครับ!")

async def delscammer_command(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str = None) -> None:
    user_id = str(update.effective_user.id)
    username = update.effective_user.username
    if not is_admin(user_id, username):
        return await update.message.reply_text("❌ ไม่มีสิทธิ์ใช้งานคำสั่งนี้")
    
    if name is None:
        name = " ".join(context.args).strip() if context.args else ""
        
    if not name:
        return await update.message.reply_text("วิธีใช้: ลบชื่อมิจ <ชื่อ>")
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scammer_database WHERE full_name = ?", (name,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted > 0:
        await update.message.reply_text(f"✅ ลบ '{name}' ออกจากฐานข้อมูลแล้ว")
    else:
        await update.message.reply_text(f"❌ ไม่พบชื่อ '{name}' ในระบบ")


async def listscammer_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    username = update.effective_user.username
    if not is_admin(user_id, username):
        return await update.message.reply_text("❌ ไม่มีสิทธิ์ใช้งานคำสั่งนี้")
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM scammer_database")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return await update.message.reply_text("📭 ยังไม่มีรายชื่อมิจฉาชีพในระบบ")
        
    names = [r[0] for r in rows]
    total_names = len(names)
    
    await update.message.reply_text(f"📋 กำลังโหลดรายชื่อมิจฉาชีพทั้งหมด ({total_names} คน)...")
    
    chunk_size = 100
    for i in range(0, total_names, chunk_size):
        chunk_names = names[i:i+chunk_size]
        msg = f"🚨 <b>รายชื่อมิจฉาชีพ (ส่วนที่ {i//chunk_size + 1}):</b>\n\n"
        msg += "\n".join([f"{i+j+1}. {n}" for j, n in enumerate(chunk_names)])
        
        if len(msg) > 4000:
            msg = msg[:4000] + "\n... (ชื่อยาวเกินไป)"
            
        await update.message.reply_html(msg)

async def addadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, target: str = None) -> None:
    user_id = str(update.effective_user.id)
    if not ADMIN_ID or user_id != ADMIN_ID:
        return await update.message.reply_text("❌ เฉพาะแอดมินหลัก (Super Admin) เท่านั้น")
        
    if target is None:
        if not context.args:
            return await update.message.reply_text("วิธีใช้: เพิ่มแอดมิน @username")
        target_username = context.args[0].replace("@", "").strip().lower()
    else:
        target_username = target.replace("@", "").strip().lower()
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO admins (username) VALUES (?)", (target_username,))
        conn.commit()
        await update.message.reply_text(f"✅ เพิ่ม @{target_username} เป็นแอดมินเรียบร้อยแล้ว")
    except sqlite3.IntegrityError:
        await update.message.reply_text("⚠️ ผู้ใช้นี้เป็นแอดมินอยู่แล้ว")
    finally:
        conn.close()

async def deladmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, target: str = None) -> None:
    user_id = str(update.effective_user.id)
    if not ADMIN_ID or user_id != ADMIN_ID:
        return await update.message.reply_text("❌ เฉพาะแอดมินหลัก (Super Admin) เท่านั้น")
        
    if target is None:
        if not context.args:
            return await update.message.reply_text("วิธีใช้: ลบแอดมิน @username หรือ ลบแอดมิน [เลข]")
        raw_target = context.args[0].strip()
    else:
        raw_target = target.strip()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if raw_target.isdigit():
        idx = int(raw_target)
        cursor.execute("SELECT username FROM admins ORDER BY rowid ASC")
        rows = cursor.fetchall()
        if 1 <= idx <= len(rows):
            target_username = rows[idx-1][0]
        else:
            conn.close()
            return await update.message.reply_text(f"❌ ไม่มีแอดมินลำดับที่ {idx}")
    else:
        target_username = raw_target.replace("@", "").lower()
        
    cursor.execute("DELETE FROM admins WHERE username = ?", (target_username,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted > 0:
        await update.message.reply_text(f"✅ ลบ @{target_username} ออกจากตำแหน่งแอดมินแล้ว")
    else:
        await update.message.reply_text(f"❌ ไม่พบ @{target_username} ในรายชื่อแอดมิน")

async def adminlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if not ADMIN_ID or user_id != ADMIN_ID:
        return await update.message.reply_text("❌ เฉพาะแอดมินหลัก (Super Admin) เท่านั้น")
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM admins ORDER BY rowid ASC")
    rows = cursor.fetchall()
    conn.close()
    
    try:
        if ADMIN_ID:
            chat = await context.bot.get_chat(ADMIN_ID)
            super_name = chat.first_name or chat.username or ADMIN_ID
        else:
            super_name = "ไม่ได้ตั้งค่า"
    except Exception:
        super_name = ADMIN_ID

    msg = "👑 <b>Super Admin:</b>\n" + f"1. {super_name}\n\n"
    msg += "👮 <b>Admins:</b>\n"
    if rows:
        msg += "\n".join([f"{i+1}. @{r[0]}" for i, r in enumerate(rows)])
    else:
        msg += "- ไม่มี -"
        
    await update.message.reply_html(msg)

def check_name_in_db(name: str, user_id: str, username: str) -> str:
    """Check name against database and return the formatted result."""
    conn = get_connection()
    cursor = conn.cursor()
    
    name = name.strip()
    if not name:
        return ""

    result_message = f"🔍 <b>ผลการตรวจสอบรายชื่อ:</b>\n👤 ชื่อ: {name}\n\n"
    
    # 1. Check if name is in scammer DB
    cursor.execute("SELECT description, severity FROM scammer_database WHERE full_name LIKE ?", (f"%{name}%",))
    scammer_record = cursor.fetchone()
    
    if scammer_record:
        desc, severity = scammer_record
        result_message += f"⚠️ <b>สถานะ:</b> 🔴 <b>ตรวจพบมิจฉาชีพ!</b>\n"
        result_message += f"📝 <b>รายละเอียด:</b> {desc}\n"
        conn.close()
        return result_message # Stop here, don't save to search_history
    
    # 2. Check if name was previously searched
    cursor.execute("SELECT username, searched_at FROM search_history WHERE search_name = ? ORDER BY searched_at DESC LIMIT 1", (name,))
    history_record = cursor.fetchone()
    
    if history_record:
        searched_by, searched_at = history_record
        result_message += f"⚠️ <b>ลูกค้าเก่า!:</b> 🟡 มีการส่งชื่อและบันทึกไว้แล้ว (เวลา {searched_at})\n"
    else:
        result_message += f"✅ <b>สถานะ:</b> 🟢 เป็นลูกค้าใหม่ บันทึกรายชื่อลงระบบเรียบร้อยแล้ว\n"
        # 3. Log this search only if new
        cursor.execute(
            "INSERT INTO search_history (user_id, username, search_name) VALUES (?, ?, ?)",
            (str(user_id), username, name)
        )
        conn.commit()

    conn.close()
    
    return result_message

def batch_process_names(names: list, user_id: str, username: str) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    
    new_customers = []
    duplicates = []
    scammers = []
    
    for name in names:
        # 1. Check scammer
        cursor.execute("SELECT description FROM scammer_database WHERE full_name LIKE ?", (f"%{name}%",))
        scammer_record = cursor.fetchone()
        if scammer_record:
            scammers.append((name, scammer_record[0]))
            continue
            
        # 2. Check duplicate
        cursor.execute("SELECT username FROM search_history WHERE search_name = ? ORDER BY searched_at DESC LIMIT 1", (name,))
        history_record = cursor.fetchone()
        if history_record:
            duplicates.append(name)
        else:
            new_customers.append(name)
            cursor.execute(
                "INSERT INTO search_history (user_id, username, search_name) VALUES (?, ?, ?)",
                (str(user_id), username, name)
            )
            
    conn.commit()
    conn.close()
    
    msg_parts = []
    if new_customers:
        msg_parts.append("✅ <b>บันทึกลูกค้าใหม่:</b>")
        for i, n in enumerate(new_customers, 1):
            msg_parts.append(f"{i}. {n}")
        msg_parts.append("")
        
    if duplicates:
        msg_parts.append("⚠️ <b>ลูกค้าเก่า (มีในระบบแล้ว):</b>")
        for i, n in enumerate(duplicates, 1):
            msg_parts.append(f"{i}. {n}")
        msg_parts.append("")
        
    if scammers:
        msg_parts.append("🔴 <b>เตือนภัย! พบมิจฉาชีพ:</b>")
        for i, (n, desc) in enumerate(scammers, 1):
            msg_parts.append(f"{i}. {n} ({desc})")
            
    return "\n".join(msg_parts).strip()

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all saved non-scammer customers."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT search_name FROM search_history GROUP BY search_name ORDER BY MAX(id) DESC")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return await update.message.reply_text("📭 ยังไม่มีรายชื่อลูกค้าในระบบ")
        
    names = [r[0] for r in rows]
    total_names = len(names)
    
    await update.message.reply_text(f"📋 กำลังโหลดรายชื่อลูกค้าทั้งหมด ({total_names} คน)...")
    
    chunk_size = 100
    for i in range(0, total_names, chunk_size):
        chunk_names = names[i:i+chunk_size]
        msg = f"📋 <b>รายชื่อลูกค้า (ส่วนที่ {i//chunk_size + 1}):</b>\n\n"
        msg += "\n".join([f"{i+j+1}. {n}" for j, n in enumerate(chunk_names)])
        
        if len(msg) > 4000:
            msg = msg[:4000] + "\n... (ชื่อยาวเกินไป)"
            
        await update.message.reply_html(msg)

async def delete_names_by_numbers(update: Update, numbers: list) -> None:
    user_id = str(update.effective_user.id)
    username = update.effective_user.username
    if not is_admin(user_id, username):
        return await update.message.reply_text("❌ เฉพาะแอดมินเท่านั้นที่ลบรายชื่อได้")

    valid_numbers = [n for n in numbers if n >= 1]
    if not valid_numbers:
        return await update.message.reply_text("⚠️ ตัวเลขไม่ถูกต้อง")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT search_name FROM search_history GROUP BY search_name ORDER BY MAX(id) DESC")
    rows = cursor.fetchall()
    
    target_names = []
    for num in valid_numbers:
        if num <= len(rows):
            target_names.append(rows[num-1][0])
            
    if not target_names:
        conn.close()
        return await update.message.reply_text("⚠️ ไม่มีรายชื่อในลำดับที่ระบุ")

    placeholders = ",".join(["?"] * len(target_names))
    cursor.execute(f"DELETE FROM search_history WHERE search_name IN ({placeholders})", target_names)
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted > 0:
        names_str = ", ".join(target_names)
        await update.message.reply_text(f"🗑️ ลบรายชื่อ <b>{names_str}</b> ออกจากระบบเรียบร้อยแล้ว", parse_mode='HTML')
    else:
        await update.message.reply_text("⚠️ เกิดข้อผิดพลาดในการลบรายชื่อ")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages and check names."""
    text = update.message.text
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name
    
    if text.strip() == "คำสั่ง":
        await help_command(update, context)
        return
        
    if text.strip().lower() == "idm":
        await myid_command(update, context)
        return
        
    if text.strip().lower() == "idg":
        await groupid_command(update, context)
        return
        
    if text.strip().lower() == "admin":
        await adminlist_command(update, context)
        return
        
    if text.strip().startswith("ลบชื่อมิจ "):
        name = text.strip()[10:].strip()
        await delscammer_command(update, context, name)
        return
        
    if text.strip().startswith("เพิ่มแอดมิน "):
        target = text.strip()[11:].strip()
        await addadmin_command(update, context, target)
        return
        
    if text.strip().startswith("ลบแอดมิน "):
        target = text.strip()[9:].strip()
        await deladmin_command(update, context, target)
        return

    if text.strip() == "รายชื่อ":
        await list_command(update, context)
        return
        
    if text.strip() == "รายชื่อมิจ":
        await listscammer_command(update, context)
        return
        
    if text.strip().startswith(("เพิ่มชื่อมิจ", "เพิ่มรายชื่อมิจ", "เพิ่มมิจฉาชีพ")):
        if not is_admin(user_id, username):
            await update.message.reply_text("❌ เฉพาะแอดมินเท่านั้นที่เพิ่มรายชื่อมิจฉาชีพได้")
            return
            
        raw_text = text
        for cmd in ["เพิ่มชื่อมิจ", "เพิ่มรายชื่อมิจ", "เพิ่มมิจฉาชีพ"]:
            if raw_text.startswith(cmd):
                raw_text = raw_text.replace(cmd, "", 1).strip()
                break
                
        raw_names = raw_text.split('\n')
        names_to_add = []
        note = "เพิ่มผ่านระบบแชทกลุ่ม"
        for n in raw_names:
            cleaned = n.replace('"', '').replace("'", "").strip()
            if cleaned.startswith("หมายเหตุ"):
                note_text = cleaned.replace("หมายเหตุ", "", 1).strip(" :")
                if note_text:
                    note = note_text
                continue
                
            if len(cleaned) >= 2:
                names_to_add.append(cleaned)
                
        if not names_to_add:
            await update.message.reply_text("⚠️ กรุณาระบุชื่อมิจฉาชีพที่ต้องการเพิ่ม\nตัวอย่าง:\nเพิ่มชื่อมิจ\nชื่อ 1\nชื่อ 2")
            return
            
        conn = get_connection()
        cursor = conn.cursor()
        added_count = 0
        for name in names_to_add:
            cursor.execute("SELECT 1 FROM scammer_database WHERE full_name = ?", (name,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO scammer_database (full_name, bank_account, description, severity) VALUES (?, ?, ?, 'HIGH')",
                    (name, "-", note)
                )
                added_count += 1
        conn.commit()
        conn.close()
        
        if added_count > 0:
            await update.message.reply_text(f"✅ เพิ่มรายชื่อมิจฉาชีพสำเร็จ {added_count} รายการ")
        else:
            await update.message.reply_text("⚠️ ไม่มีรายชื่อถูกเพิ่ม (รายชื่ออาจมีในระบบแล้วทั้งหมด)")
        return
        
    if text.strip().startswith("ลบชื่อ "):
        try:
            nums_str = text.strip()[6:]
            nums = [int(n.strip()) for n in nums_str.split(",") if n.strip()]
            if nums:
                await delete_names_by_numbers(update, nums)
            else:
                await update.message.reply_text("⚠️ กรุณาระบุตัวเลขที่ถูกต้อง เช่น: ลบชื่อ 1 หรือ ลบชื่อ 1,2,4")
        except ValueError:
            await update.message.reply_text("⚠️ กรุณาระบุตัวเลขที่ถูกต้อง เช่น: ลบชื่อ 1 หรือ ลบชื่อ 1,2,4")
        return
    
    # Split by newline and strip quotes
    raw_names = text.split('\n')
    names = []
    for n in raw_names:
        cleaned = n.replace('"', '').replace("'", "").strip()
        if len(cleaned) >= 2:
            names.append(cleaned)
    
    if not names:
        await update.message.reply_text("กรุณาพิมพ์ชื่อที่ต้องการตรวจสอบครับ")
        return
        
    if len(names) == 1:
        reply_msg = check_name_in_db(names[0], user_id, username)
        if reply_msg:
            await update.message.reply_html(reply_msg)
    else:
        reply_msg = batch_process_names(names, user_id, username)
        if reply_msg:
            if len(reply_msg) > 4000:
                reply_msg = reply_msg[:4000] + "\n... (แสดงไม่หมด)"
            await update.message.reply_html(reply_msg)

def main() -> None:
    """Start the bot."""
    setup_database()
    
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == 'your_telegram_bot_token_here':
        logger.error("TELEGRAM_TOKEN is not set in .env file. Please set it before running.")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("myid", myid_command))
    application.add_handler(CommandHandler("groupid", groupid_command))
    application.add_handler(CommandHandler("addscammer", addscammer_command))
    application.add_handler(CommandHandler("delscammer", delscammer_command))
    application.add_handler(CommandHandler("listscammer", listscammer_command))
    application.add_handler(CommandHandler("admin", addadmin_command))
    application.add_handler(CommandHandler("deladmin", deladmin_command))
    application.add_handler(CommandHandler("adminlist", adminlist_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
