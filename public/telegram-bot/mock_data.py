import sqlite3
from database import get_connection, setup_database

def populate_mock_data():
    setup_database() # Ensure tables exist
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing mock data to avoid duplicates on multiple runs
    cursor.execute("DELETE FROM scammer_database")

    mock_scammers = [
        ("สมชาย ใจดี", "1234567890", "โกงค่าบัตรคอนเสิร์ต ไม่ยอมส่งของ", "HIGH"),
        ("มานี มีแชร์", "0987654321", "หลอกลงทุนแชร์ลูกโซ่ หนีหาย", "HIGH"),
        ("ชูใจ ร้ายลึก", "1122334455", "ขายของมือสอง โอนแล้วบล็อก", "MEDIUM")
    ]

    cursor.executemany('''
        INSERT INTO scammer_database (full_name, bank_account, description, severity)
        VALUES (?, ?, ?, ?)
    ''', mock_scammers)

    conn.commit()
    conn.close()
    print(f"Inserted {len(mock_scammers)} mock scammers into database.")

if __name__ == "__main__":
    populate_mock_data()
