import hashlib
import time
import os
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- TRUNG TÂM CẤU HÌNH HỆ THỐNG ---
config = {
    "admin_key": "hoangdz_vip_2026", # Mã bảo mật Admin
    "base_p": 915000,               # Phiên bắt đầu
    "cycle": 48.0,                  # Chu kỳ mặc định 48 giây
    "offset": 0.0,                  # Độ lệch thời gian (để đồng bộ nhanh/chậm)
    "start_time": time.time(),      # Thời điểm bắt đầu chạy
    "analyze_duration": 5           # Thời gian hiển thị "Phân tích" (giây)
}

# --- THUẬT TOÁN SOI CẦU ANTI-RANDOM ---
def solve_api_logic(p):
    """
    Dựa trên mã băm SHA-256 của phiên để đưa ra kết quả cố định.
    Không dùng hàm random để đảm bảo tính logic và ổn định.
    """
    seed = f"V24-FINAL-{p}-HOANGDZ-LC79"
    h = hashlib.sha256(seed.encode()).hexdigest()
    
    # Bóc tách xúc xắc từ chuỗi Hex
    d1 = (int(h[2:4], 16) % 6) + 1
    d2 = (int(h[12:14], 16) % 6) + 1
    d3 = (int(h[22:24], 16) % 6) + 1
    
    total = d1 + d2 + d3
    res = "TÀI" if total >= 11 else "XỈU"
    
    # TỈ LỆ THẮNG: 50% - 86% (Lấy từ mã băm, không random)
    rate_seed = int(h[60:62], 16) % 37 # Trả về 0-36
    final_rate = 50 + rate_seed        # Kết quả: 50% -> 86%
    
    return [d1, d2, d3], total, res, f"{final_rate}%"

# --- GIAO DIỆN QUẢN LÝ (ADMIN PANEL) ---
ADMIN_HTML = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HOANGDZ - V24 ADMIN</title>
    <style>
        body { background: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .box { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 25px; width: 340px; box-shadow: 0 10px 40px rgba(0,0,0,0.6); text-align: center; }
        h2 { color: #58a6ff; font-size: 18px; margin-bottom: 20px; border-bottom: 1px solid #30363d; padding-bottom: 10px; text-transform: uppercase; }
        .row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        label { font-size: 12px; color: #8b949e; text-transform: uppercase; }
        input { background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: white; padding: 8px; width: 120px; text-align: center; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }
        button { padding: 12px; border-radius: 6px; border: none; font-weight: bold; cursor: pointer; transition: 0.2s; }
        .btn-sync { background: #238636; color: white; grid-column: span 2; font-size: 14px; }
        .btn-sync:hover { background: #2ea043; }
        .btn-adj { background: #30363d; color: #c9d1d9; font-size: 12px; }
        .btn-adj:hover { background: #58a6ff; color: white; }
        #status { margin-top: 15px; font-size: 13px; color: #7ee787; font-style: italic; }
        .offset-val { color: #ffab70; font-weight: bold; }
    </style>
</head>
<body>
    <div class="box">
        <h2>SENTINEL V24 ADMIN</h2>
        <div class="row">
            <label>Phiên hiện tại</label>
            <input type="number" id="p" placeholder="915xxx">
        </div>
        <div class="row">
            <label>Chu kỳ (giây)</label>
            <input type="number" id="c" value="48" step="0.1">
        </div>
        <div class="row">
            <label>Độ lệch (Offset)</label>
            <span class="offset-val" id="o_val">0.0s</span>
        </div>
        
        <div class="btn-group">
            <button class="btn-adj" onclick="adjust(-0.1)">- 0.1s (Nhanh hơn)</button>
            <button class="btn-adj" onclick="adjust(0.1)">+ 0.1s (Chậm lại)</button>
            <button class="btn-sync" onclick="send()">ĐỒNG BỘ TOÀN HỆ THỐNG</button>
        </div>
        <div id="status">Hệ thống đang chờ lệnh...</div>
    </div>

    <script>
        let currentOffset = 0.0;

        function adjust(val) {
            currentOffset = parseFloat((currentOffset + val).toFixed(1));
            document.getElementById('o_val').innerText = currentOffset + "s";
            send(); // Tự động cập nhật khi chỉnh tốc độ
        }

        async function send() {
            const statusBox = document.getElementById('status');
            statusBox.innerText = "Đang đồng bộ...";
            
            const payload = {
                p: document.getElementById('p').value,
                c: document.getElementById('c').value,
                o: currentOffset
            };

            try {
                const res = await fetch('/admin/update', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                const d = await res.json();
                statusBox.innerText = "✓ " + d.msg;
            } catch (e) {
                statusBox.innerText = "❌ Lỗi kết nối API!";
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(ADMIN_HTML)

@app.route('/admin/update', methods=['POST'])
def update_config():
    data = request.json
    if data.get("p"): config["base_p"] = int(data.get("p"))
    config["cycle"] = float(data.get("c", 48.0))
    config["offset"] = float(data.get("o", 0.0))
    config["start_time"] = time.time() # Reset mốc thời gian để khớp phiên mới
    return jsonify({"msg": f"Đã đồng bộ nhịp {config['cycle']}s (Offset: {config['offset']}s)"})

@app.route('/api/data', methods=['GET'])
def get_api():
    now = time.time()
    # Tính thời gian trôi qua có bù trừ độ lệch offset
    real_elapsed = (now - config["start_time"]) - config["offset"]
    
    # Tính phiên hiện tại
    passed_phiens = int(real_elapsed // config["cycle"])
    curr_p = config["base_p"] + passed_phiens
    
    # Tính thời gian đếm ngược
    countdown = config["cycle"] - (real_elapsed % config["cycle"])
    
    # 1. GIAI ĐOẠN PHÂN TÍCH (5 giây đầu mỗi phiên)
    if countdown > (config["cycle"] - config["analyze_duration"]):
        time_left = round(countdown - (config["cycle"] - 5), 1)
        return jsonify({
            "phien": curr_p,
            "countdown": round(countdown, 1),
            "du_doan": f"ĐANG PHÂN TÍCH ({time_left}s)",
            "ti_le": "CALCULATING...",
            "status": "ANALYZING",
            "xuc_xac": [0,0,0]
        })
    
    # 2. GIAI ĐOẠN HIỂN THỊ KẾT QUẢ (Sau 5 giây phân tích)
    dice, total, pred, rate = solve_api_logic(curr_p)
    return jsonify({
        "phien": curr_p,
        "countdown": round(countdown, 1),
        "du_doan": pred,
        "ti_le": rate,
        "xuc_xac": dice,
        "tong_diem": total,
        "status": "LIVE"
    })

if __name__ == '__main__':
    # Chạy trên port Render hoặc mặc định 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
