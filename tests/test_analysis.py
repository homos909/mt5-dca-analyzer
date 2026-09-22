import sys
import os
# Them thu muc src/ vao duong dan tim module, de import duoc analysis.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from analysis import find_chain_root, calculate_chain_drawdown


def test_find_chain_root_single_position():
    # Truong hop don gian: 1 lenh khong co DCA (khong co cha)
    by_id = {
        100: {"dca_chain_root": None}
    }
    result = find_chain_root(100, by_id)
    assert result == 100   # lenh goc phai tra ve chinh no


def test_find_chain_root_multi_level_chain():
    # Truong hop chuoi nhieu tang: 300 -> 200 -> 100 (100 la goc that su)
    by_id = {
        100: {"dca_chain_root": None},
        200: {"dca_chain_root": 100},
        300: {"dca_chain_root": 200},
    }
    result = find_chain_root(300, by_id)
    # TODO: ket qua mong doi la gi? (chinh la ID cua lenh GOC THAT SU, sau khi truy het chuoi)
    assert result == 100


def test_calculate_chain_drawdown_no_dip():
    # Truong hop: lien tuc co loi, khong bao gio am -> drawdown phai la 0
    positions = [
        {"time_open": "2025.01.01 10:00:00", "net_profit": 5},
        {"time_open": "2025.01.02 10:00:00", "net_profit": 3},
    ]
    result = calculate_chain_drawdown(positions)
    assert result == 0


def test_calculate_chain_drawdown_with_dip():
    # Truong hop giong chuoi 174920672 thuc te: lo sau roi moi hoi phuc
    positions = [
        {"time_open": "2025.01.01 10:00:00", "net_profit": -10},
        {"time_open": "2025.01.02 10:00:00", "net_profit": -20},   # cong don: -30 (diem thap nhat)
        {"time_open": "2025.01.03 10:00:00", "net_profit": 50},    # hoi phuc, cong don: +20
    ]
    result = calculate_chain_drawdown(positions)
    # TODO: ket qua mong doi la gi? (chinh la diem THAP NHAT trong qua trinh cong don)
    assert result == -30