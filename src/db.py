
import os
from dotenv import load_dotenv
import psycopg2
from ingest import read_file, parse_tables, find_section_rows, parse_position_row, resolve_chain_roots
from config import DB_PATH, RAW_HTML_PATH

load_dotenv()  # đọc file .env, nạp DATABASE_URL vào os.environ

def get_connection():
    """Mở kết nối tới PostgreSQL, trả về connection object."""
    # TODO: lấy giá trị DATABASE_URL từ biến môi trường
    # gợi ý: dùng os.environ.get("...")
    db_url = os.environ.get("DATABASE_URL")

    # TODO: dùng psycopg2.connect() để mở kết nối
    # gợi ý: psycopg2.connect() có thể nhận thẳng 1 connection string qua tham số `dsn`
    conn = psycopg2.connect(dsn=db_url)
   
    return conn

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            position_id INTEGER PRIMARY KEY,
            time_open TEXT,
            time_close TEXT,
            symbol TEXT,
            type TEXT,
            comment TEXT,
            volume REAL,
            price_open REAL,
            price_close REAL,
            commission REAL,
            swap REAL,
            profit REAL,
            net_profit REAL,
            is_dca INTEGER,
            dca_sequence INTEGER,
            dca_chain_root INTEGER
        )
    """)
    conn.commit()

def migrate_table(conn):
    cursor = conn.cursor()

    # TODO: viết câu query lấy tên các cột hiện có từ information_schema.columns
    # gợi ý cú pháp: SELECT column_name FROM information_schema.columns WHERE table_name = 'positions'
    cursor.execute(""" SELECT column_name FROM information_schema.columns WHERE table_name= 'positions' """)
    existing_columns = [row[0] for row in cursor.fetchall()]
    # Lưu ý: row[0] chứ không phải row[1] như PRAGMA — vì SELECT chỉ lấy 1 cột (column_name),
    # nên nó nằm ở vị trí 0 của tuple, không phải vị trí 1

    required_columns = {
        "net_profit": "REAL",
    }

    for col_name, col_type in required_columns.items():
        if col_name not in existing_columns:
            print(f"Dang them cot con thieu: {col_name}")
            cursor.execute(f"ALTER TABLE positions ADD COLUMN {col_name} {col_type}")

    conn.commit()

def insert_positions(conn, positions):
    cursor = conn.cursor()
    for record in positions:
        cursor.execute("""
            INSERT INTO positions
            (position_id, time_open, time_close, symbol, type, comment,
             volume, price_open, price_close, commission, swap, profit, net_profit,
             is_dca, dca_sequence, dca_chain_root)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (position_id) DO UPDATE SET
                time_open = EXCLUDED.time_open,
                time_close = EXCLUDED.time_close,
                symbol = EXCLUDED.symbol,
                type = EXCLUDED.type,
                comment = EXCLUDED.comment,
                volume = EXCLUDED.volume,
                price_open = EXCLUDED.price_open,
                price_close = EXCLUDED.price_close,
                commission = EXCLUDED.commission,
                swap = EXCLUDED.swap,
                profit = EXCLUDED.profit,
                net_profit = EXCLUDED.net_profit,
                is_dca = EXCLUDED.is_dca,
                dca_sequence = EXCLUDED.dca_sequence,
                dca_chain_root = EXCLUDED.dca_chain_root
        """, (
            int(record["position_id"]), record["time_open"], record["time_close"], record["symbol"], record["type"], record["comment"], float(record["volume"]),
            float(record["price_open"]), float(record["price_close"]), float(record["commission"]), float(record["swap"]), float(record["profit"]), float(record["net_profit"]), int(record["is_dca"]),
            int(record["dca_sequence"]) if record["dca_sequence"] else None, int(record["dca_chain_root"]) if record["dca_chain_root"] else None
        ))  # (không cần dòng cho position_id, vì đó là cột dùng để so khớp "conflict")    

    conn.commit()    

if __name__ == "__main__":
    
    file_path = "data/raw/ReportHistory-158324.html"
    result = read_file(file_path)

    if result["success"]:
        tables = parse_tables(result["content"])
        table = tables[0]
        start_idx = find_section_rows(table, "Positions")
        end_idx = find_section_rows(table, "Orders")
        all_rows = table.find_all("tr")
        data_rows = all_rows[start_idx + 2:end_idx]

        positions = []
        for row in data_rows:
            cells = row.find_all("td")
            if len(cells) < 14:
                continue
            positions.append(parse_position_row(row))

        positions = resolve_chain_roots(positions)    
        conn = get_connection()
        create_table(conn)
        migrate_table(conn)
        insert_positions(conn, positions)

        conn.close()

        print(f"Da luu {len(positions)} positions vao PostgreSQL (Neon)")