
import sqlite3
from ingest import read_file, parse_tables, find_section_rows, parse_position_row
from config import DB_PATH, RAW_HTML_PATH

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

    # Lay danh sach cot HIEN CO trong bang
    cursor.execute("PRAGMA table_info(positions)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    # row[1] la vi tri chua TEN COT trong ket qua PRAGMA — moi dong la 1 tuple
    # (cid, name, type, notnull, dflt_value, pk)

    # Danh sach cot MONG MUON, dang { ten_cot: kieu_du_lieu }
    required_columns = {
        "net_profit": "REAL",
        # TODO: neu sau nay them cot moi, chi can khai bao them o day

    }

    for col_name, col_type in required_columns.items():
        if col_name not in existing_columns:
            print(f"Dang them cot con thieu: {col_name}")
            # TODO: viet cau lenh ALTER TABLE de them cot nay vao bang "positions"
            # Cu phap SQL: ALTER TABLE positions ADD COLUMN <ten_cot> <kieu_du_lieu>
            cursor.execute(f"ALTER TABLE positions ADD COLUMN {col_name} {col_type}")

    conn.commit()

def insert_positions(conn, positions):
    cursor = conn.cursor()
    for record in positions:
        cursor.execute("""
            INSERT OR REPLACE INTO positions
            (position_id, time_open, time_close, symbol, type, comment,
             volume, price_open, price_close, commission, swap, profit, net_profit,
             is_dca, dca_sequence, dca_chain_root)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(record["position_id"]), record["time_open"], record["time_close"], record["symbol"], record["type"], record["comment"], float(record["volume"]),
            float(record["price_open"]), float(record["price_close"]), float(record["commission"]), float(record["swap"]), float(record["profit"]), float(record["net_profit"]), int(record["is_dca"]),
            int(record["dca_sequence"]) if record["dca_sequence"] else None, int(record["dca_chain_root"]) if record["dca_chain_root"] else None # TODO: đưa đúng 15 giá trị vào đây, đúng thứ tự các cột ở trên
        ))
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

        conn = sqlite3.connect(DB_PATH)
        create_table(conn)
        migrate_table(conn)
        insert_positions(conn, positions)

        conn.close()

        print(f"Da luu {len(positions)} positions vao {DB_PATH}")