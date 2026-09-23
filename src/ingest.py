from pathlib import Path
from bs4 import BeautifulSoup
import re
import json

def read_file(file_path, encodings=None):
    if encodings is None:
        encodings = ["utf-8", "utf-16"]

    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            return {
                "success": True,
                "path": str(Path(file_path).resolve()),
                "encoding": enc,
                "content": content
            }
        except Exception as e:
            print(f"Loi doc voi encoding '{enc}': {e}")
            # KHONG return o day -> vong for tu dong thu encoding tiep theo

    # Chi chay toi day khi TAT CA encoding trong list deu that bai
    return{
        "success": False,    
        "message": f"Khong doc duoc file voi cac encoding: {encodings}"
    }



def parse_tables(html_content):
    soup = BeautifulSoup(html_content, "lxml")
    tables = soup.find_all("table")       # TODO: dùng soup để tìm TẤT CA các thẻ <table>
    print("So luong table:", len(tables))   # TODO: in ra số lượng table tìm được
    return tables

def find_section_rows(table, section_name):
    all_rows = table.find_all("tr")

    start_index = None
    for i, row in enumerate(all_rows):
        cells = row.find_all(["td", "th"])
        # TODO: kiểm tra điều kiện: dòng này có đúng 1 cell,
        # và text của cell đó (dùng .get_text(strip=True)) đúng bằng section_name?
        if len(cells) == 1 and cells[0].get_text(strip=True) == section_name:
            start_index = i
            break

    print(f"Tim thay '{section_name}' o dong index:", start_index)
    return start_index  

def parse_dca_info(comment):
    # Truong hop 1: la lenh DCA, dang "D*CA-S [3]#135656315" hoac "D*CA-B [1]#..."
    match = re.match(r"D\*CA-[SB] \[(\d+)\]#(\d+)", comment)
    if match:
        return {
            "is_dca": True,
            "dca_sequence": match.group(1),     # TODO: lay tu match, nhom (group) so may?
            "dca_chain_root": match.group(2),   # TODO: lay tu match, nhom (group) so may?
        }

    # Truong hop 2: la lenh goc (khong phai DCA)
    return {
        "is_dca": False,
        "dca_sequence": None,
        "dca_chain_root": None,
    }  

def parse_position_row(row):
    cells = row.find_all("td")
    texts = [c.get_text(strip=True) for c in cells]

    # TODO: texts là 1 list có 14 phần tử, theo đúng thứ tự cột đã liệt kê ở trên
    # Hãy gán từng phần tử vào đúng tên biến, dùng cách lấy theo chỉ số (index)
    # Vi du: time_open = texts[0]

    record = {
        "time_open": texts[0],
        "position_id": texts[1],
        "symbol": texts[2],
        "type": texts[3],
        "comment": texts[4],
        "volume": texts[5],
        "price_open": texts[6],
        "S/L":texts[7],
        "T/P": texts[8],
        "time_close": texts[9],
        "price_close": texts[10],
        "commission": texts[11],
        "swap": texts[12],
        "profit": texts[13]
    }
    # TODO: gọi parse_dca_info với đúng giá trị comment của record này,
    # rồi gộp kết quả (dict trả về) vào record bằng record.update(...)
    dca_info = parse_dca_info(record["comment"])
    record.update(dca_info)
    record["net_profit"] = float(record["profit"]) + float(record["commission"]) + float(record["swap"])
    return record

def resolve_chain_roots(positions):
    """Sau khi có đủ tất cả positions, đi lại một lượt để sửa dca_chain_root
    từ 'con trỏ tới lệnh ngay trước' thành 'gốc thật sự của cả chain'."""

    # TODO: tạo dict tra cứu nhanh: key là position_id (string), value là record đó
    # gợi ý: dict comprehension —  {record["position_id"]: record for record in ...}
    lookup = {record["position_id"]: record for record in positions}

    for record in positions:
        if not record["is_dca"]:
            continue  # lệnh gốc, dca_chain_root vốn đã là None, không cần sửa

        pointer = record["dca_chain_root"]  # bắt đầu từ con trỏ hiện tại

        # TODO: viết vòng lặp while — lặp tiếp chừng nào lệnh mà `pointer`
        # đang trỏ tới (tức lookup[pointer]) VẪN LÀ một lệnh DCA khác
        # (lookup[pointer]["is_dca"] == True), thì cập nhật:
        #   pointer = lookup[pointer]["dca_chain_root"]
        # rồi lặp tiếp, cho tới khi lookup[pointer]["is_dca"] == False
        while pointer in lookup and lookup[pointer]["is_dca"]:
            pointer = lookup[pointer]["dca_chain_root"]

        record["dca_chain_root"] = pointer  # gán lại gốc thật đã truy vết được

    return positions 

if __name__ == "__main__":
    file_path = "data/raw/ReportHistory-158324.html"
    result = read_file(file_path)

    if result["success"]:
        tables = parse_tables(result["content"]) # TODO: gọi hàm parse_tables với đúng dữ liệu cần
        table = tables[0]

        start_idx = find_section_rows(table, "Positions")
        end_idx = find_section_rows(table, "Orders")   # TODO: gọi lại find_section_rows, nhưng tìm section nào?

        all_rows = table.find_all("tr")
        # Dữ liệu thật nằm sau: dòng section title (start_idx),
        # rồi 1 dòng header cột (start_idx + 1),
        # nên dữ liệu bắt đầu từ start_idx + 2, kết thúc trước end_idx
        data_rows = all_rows[start_idx + 2 : end_idx]   # TODO: cắt list bằng slicing, từ đâu đến đâu?

        print("So dong du lieu Positions:", len(data_rows))
    else:
        print(result["message"])

        
    data_rows = all_rows[start_idx + 2:end_idx]
    #first_record = parse_position_row(data_rows[0])
    #print(first_record)

    positions = []
    for row in data_rows:
        cells = row.find_all("td")
        if len(cells) < 14:
            # TODO: đây là dòng rác (dòng trống), in ra 1 thông báo rồi bỏ qua dòng này
            # Gợi ý: dùng "continue" để nhảy sang vòng lặp kế tiếp, không parse dòng này
            print("Đã bỏ qua các dòng rác")
            continue

        record = parse_position_row(row)   # TODO: gọi parse_position_row với đúng biến đang lặp
        positions.append(record)

    print("Tong so position da parse:", len(positions))   # TODO: đếm số phần tử trong positions
    print("Position dau tien:", positions[0])
    print("Position cuoi cung:", positions[-1])

    print(json.dumps(positions[2], indent=2, ensure_ascii=False))