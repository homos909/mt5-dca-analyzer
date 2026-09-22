import sqlite3
from config import DB_PATH, RAW_HTML_PATH
from datetime import datetime
from collections import defaultdict

def load_positions(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM positions")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    # Chuyen moi dong (tuple) thanh dict, de de thao tac hon
    positions = [dict(zip(columns, row)) for row in rows]
    return positions


def find_chain_root(position_id, by_id):
    """Truy nguoc len den lenh GOC (khong con dca_chain_root)."""
    current_id = position_id
    while by_id[current_id]["dca_chain_root"] is not None:
        current_id = (by_id[current_id]["dca_chain_root"]) # TODO: nhay len lenh cha, dua vao du lieu cua current_id
    return current_id

def build_chains(positions, by_id):
    chains = {}   # { chain_root_id: [list cac position thuoc chain do] }

    for p in positions:
        root = find_chain_root(p["position_id"], by_id)
        if root not in chains:
            chains[root] = []
        chains[root].append(p)

    return chains

def calculate_chain_drawdown(chain_positions):
    # Sap xep lai theo dung thu tu thoi gian mo lenh (phong truong hop DB tra ve khac thu tu)
    sorted_positions = sorted(chain_positions, key=lambda p: p["time_open"])

    running_total = 0
    worst_point = 0
    for p in sorted_positions:
        running_total += p["net_profit"]
        if running_total < worst_point:
            worst_point = running_total   # TODO: cap nhat worst_point bang gia tri nao?

    return round(worst_point, 2)

def parse_time(time_str):
    # Dinh dang trong file MT5: "2026.05.12 10:54:01" -> nam.thang.ngay gio:phut:giay
    return datetime.strptime(time_str, "%Y.%m.%d %H:%M:%S")

def group_by_weekday(chain_summaries):
    by_weekday = defaultdict(list)
    for chain in chain_summaries:
        by_weekday[chain["entry_weekday"]].append(chain["net_profit"])

    weekday_names = ["Thu 2", "Thu 3", "Thu 4", "Thu 5", "Thu 6", "Thu 7", "CN"]

    for day_num in sorted(by_weekday.keys()):
        profits = by_weekday[day_num]
        avg = sum(profits) / len(profits)
        print(f"{weekday_names[day_num]}: {len(profits)} chuoi, trung binh {avg:.2f}")

def summarize_chain(chain_positions):
    total_net_profit = sum(p["net_profit"] for p in chain_positions)
    num_layers = len(chain_positions)
    total_volume = sum(p["volume"] for p in chain_positions)
    max_drawdown = calculate_chain_drawdown(chain_positions) 

    # Lay thoi diem mo lenh cua LAYER DAU TIEN (chinh la thoi diem quyet dinh vao lenh)
    sorted_positions = sorted(chain_positions, key=lambda p: p["time_open"])
    entry_time = parse_time(sorted_positions[0]["time_open"])

    # TODO: tinh exit_time - thoi diem DONG MUON NHAT trong ca chuoi
    # Goi y: dung max(), voi key la ham parse_time ap dung len p["time_close"] cua tung layer
    exit_time = max(parse_time(p["time_close"]) for p in chain_positions)

    return {
        "root_id": chain_positions[0]["dca_chain_root"] or chain_positions[0]["position_id"],
        "num_layers": num_layers,
        "total_volume": round(total_volume, 2),
        "net_profit": round(total_net_profit, 2),
        "max_drawdown": max_drawdown,
        "symbol": chain_positions[0]["symbol"],
        "entry_hour": entry_time.hour,      # TODO: lay gio (0-23) tu entry_time
        "entry_weekday": entry_time.weekday(),   # TODO: lay thu trong tuan tu entry_time
        "exit_time": exit_time
    }


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    positions = load_positions(conn)
    by_id = {p["position_id"]: p for p in positions}

    chains = build_chains(positions, by_id)

    chain_summaries = [summarize_chain(v) for v in chains.values()]

    print(f"Tong so chuoi giao dich thuc te: {len(chain_summaries)}")
    print(f"(So voi {len(positions)} lenh rieng le neu khong gop chain)")

    win_chains = [c for c in chain_summaries if c["net_profit"] > 0]
    loss_chains = [c for c in chain_summaries if c["net_profit"] < 0]
    print(f"Chuoi thang: {len(win_chains)}, Chuoi thua: {len(loss_chains)}")


    print(f"Tong so chuoi giao dich thuc te: {len(chain_summaries)}")
    print(f"Chuoi thang: {len(win_chains)}, Chuoi thua: {len(loss_chains)}")

    print("\n--- Chi tiet chuoi bi lo ---")
    for chain in loss_chains:
        print(chain)
        # In ra tung lenh (layer) trong chuoi do de xem chi tiet
        root_id = chain["root_id"]   # TODO: lay dung id cua chain nay
        for p in chains[root_id]:
            print(f"  {p['position_id']} | {p['time_open']} | vol={p['volume']} | net_profit={p['net_profit']}")

    print("\n--- Thong ke drawdown toan bo 29 chuoi ---")
    for chain in chain_summaries:
        print(chain)

    worst_chain = min(chain_summaries, key=lambda c: c["max_drawdown"])
    print(f"\nChuoi co drawdown sau nhat: {worst_chain}")  
    group_by_weekday(chain_summaries)      

    