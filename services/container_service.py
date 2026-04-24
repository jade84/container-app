from db import query_all
from datetime import date
from db import query_one, query_all, execute
import re
from datetime import datetime, date

def get_container_list(query=None, line=None):
    sql = "SELECT * FROM containers WHERE date_out IS NULL"
    params = []

    if query:
        sql += " AND container_no LIKE %s"
        params.append('%' + query.upper() + '%')

    if line:
        sql += " AND shipping_line LIKE %s"
        params.append('%' + line + '%')

    rows = query_all(sql, params)

    data = []
    for row in rows:
        if row['date_in']:
            days = (date.today() - row['date_in']).days
            row['days'] = days if days > 0 else 1
        else:
            row['days'] = ''

        data.append(row)

    return data


def get_shipping_lines():
    rows = query_all("SELECT DISTINCT shipping_line FROM containers")
    return [row['shipping_line'] for row in rows]

def get_container_history():
    from datetime import date

    rows = query_all("""
        SELECT * FROM containers
        WHERE date_out IS NOT NULL
        ORDER BY date_out DESC
    """)

    data = []
    for row in rows:
        if row['date_in'] and row['date_out']:
            days = (row['date_out'] - row['date_in']).days
            row['days'] = days if days >= 0 else 0
        else:
            row['days'] = ''

        data.append(row)

    return data

def find_container(container_no):
    return query_one("""
        SELECT id, container_no, shipping_line, size, status, date_in, date_out
        FROM containers
        WHERE container_no=%s
    """, (container_no,))
def export_container(container_no, booking_no, customer_name):
    # lấy container
    row = query_one("""
        SELECT id, date_out
        FROM containers
        WHERE container_no=%s
    """, (container_no,))

    if not row:
        return {"error": "Không tìm thấy container!"}

    if row['date_out']:
        return {"error": "Container đã xuất rồi!"}

    execute("""
        UPDATE containers
        SET booking_no=%s,
            customer_name=%s,
            date_out=NOW()
        WHERE container_no=%s
    """, (booking_no, customer_name, container_no))

    return {"success": "Xuất container thành công!"}



def create_container(container_no, shipping_line, size, status, date_in):
    
    container_no = container_no.upper().strip()

    # ❗ CHECK RỖNG
    if not all([container_no, shipping_line, size, status, date_in]):
        return {"error": "Vui lòng nhập đầy đủ thông tin!"}

    # ❗ CHECK ISO
    if not re.match(r'^[A-Z]{4}\d{7}$', container_no):
        return {"error": "Sai định dạng container!"}

    # ❗ CHECK TRÙNG
    existing = query_one("""
        SELECT id FROM containers
        WHERE container_no=%s AND date_out IS NULL
    """, (container_no,))

    if existing:
        return {"error": f"Container {container_no} đang tồn bãi!"}

    # ❗ CHECK NGÀY
    input_date = datetime.strptime(date_in, "%Y-%m-%d").date()

    if input_date > date.today():
        return {"error": "Date In không hợp lệ!"}

    # ✅ INSERT
    execute("""
        INSERT INTO containers (container_no, shipping_line, size, status, date_in)
        VALUES (%s, %s, %s, %s, %s)
    """, (container_no, shipping_line, size, status, date_in))

    return {"success": "Thêm container thành công!"}