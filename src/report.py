import csv
import sqlite3
from analysis import load_positions, build_chains, summarize_chain
from config import DB_PATH, OUTPUT_PATH

def export_to_csv(chain_summaries, output_path):
    if not chain_summaries:
        print("Khong co du lieu de xuat.")
        return

    fieldnames = list(chain_summaries[0].keys())
    # TODO: mo file tai output_path o che do ghi ("w"), dung csv.DictWriter
    # de ghi header (writeheader) va tung dong du lieu (writerows)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        write = csv.DictWriter(f, fieldnames=fieldnames)
        write.writeheader()
        write.writerows(chain_summaries)

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    positions = load_positions(conn)
    by_id = {p["position_id"]: p for p in positions}
    chains = build_chains(positions, by_id)
    chain_summaries = [summarize_chain(v) for v in chains.values()]
    conn.close()

    export_to_csv(chain_summaries, OUTPUT_PATH)
    print(f"Da xuat {len(chain_summaries)} chuoi ra file {OUTPUT_PATH}")