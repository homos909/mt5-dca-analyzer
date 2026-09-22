import sqlite3
import matplotlib.pyplot as plt
from analysis import load_positions, build_chains, summarize_chain
from config import DB_PATH

def plot_equity_curve(chain_summaries):
    # Sap xep chuoi theo thu tu THOI GIAN DONG (khong phai mo), vi day la luc P/L duoc "chot"
    # TODO: dung sorted(), key la gi de sap xep dung theo thoi gian?
    sorted_chains = sorted(chain_summaries, key=lambda c: c["exit_time"])

    cumulative = 0
    equity_points = []
    for chain in sorted_chains:
        cumulative += chain["net_profit"]
        equity_points.append(cumulative)

    plt.figure(figsize=(10, 5))
    plt.plot(equity_points, marker="o")
    plt.title("Duong cong loi nhuan tich luy theo tung chuoi DCA")
    plt.xlabel("Thu tu chuoi giao dich")
    plt.ylabel("Loi nhuan tich luy (USD)")
    plt.grid(True)
    plt.savefig("equity_curve.png")
    print("Da luu bieu do: equity_curve.png")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    positions = load_positions(conn)
    by_id = {p["position_id"]: p for p in positions}
    chains = build_chains(positions, by_id)
    chain_summaries = [summarize_chain(v) for v in chains.values()]
    conn.close()

    plot_equity_curve(chain_summaries)