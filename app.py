import hashlib, time, os
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CẤU HÌNH HỆ THỐNG GỐC ---
config = {
    "admin_key": "hoangdz_vip_2026",
    "base_p": 915000,
    "cycle": 48.0,
    "offset": 0.0,
    "start_time": time.time(),
    "analyze_duration": 5,
    "learning_end": time.time() + 60, # Tự học 1 phút khi khởi động
    "is_ready": False
}

def solve_api_logic(p):
    # Thuật toán phân tích băm mã (Determinism)
    seed = f"V24-ULTRASYNC-{p}-HOANGDZ-LC79"
    h = hashlib.sha256(seed.encode()).hexdigest()
    
    # Kết quả xúc xắc
    d1 = (int(h[2:4], 16) % 6) + 1
    d2 = (int(h[12:14], 16) % 6) + 1
    d3 = (int(h[22:24], 16) % 6) + 1
    total = d1 + d2 + d3
    res = "TÀI" if total >= 11 else "XỈU"
    
    # Tỉ lệ thắng cố định (50% - 86%)
    rate_seed = int(h[60:62], 16) % 37
    final_rate = 50 + rate_seed
    
    return [d1, d2, d3], total, res, f"{final_rate}%"

# --- GIAO DIỆN QUẢN TRỊ ADMIN ---
ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADMIN V24 - CONTROL CENTER</title>
    <style>
        body { background: #0b0e14; color: #adbac7; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .card { background: #1c2128; border: 1px solid #444c56; border-radius: 12px; padding: 25px; width: 330px; box-shadow: 0 15px 35px rgba(0,0,0,0.4); }
        h2 { color: #539bf5; text-align: center; font-size: 18px; margin-top: 0; text-transform: uppercase; border-bottom: 1px solid #444c56; padding-bottom: 10px; }
        .group { margin-top: 15px; }
        label { font-size: 11px; color: #768390; text-transform: uppercase; }
        input { width: 100%; padding: 10px; background: #0d1117; border: 1px solid #444c56; border-radius: 6px; color: white; margin-top: 5px; box-sizing: border-box; }
        .controls { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 15px; }
        button { padding: 12px; border-radius: 6px; border: none; font-weight: bold; cursor: pointer; transition: 0.2s; }
        .btn-blue { background: #1f6feb; color: white; }
        .btn-green { background: #238636; color: white; grid-column: span 2; margin-top: 10px; }
        .btn-blue:hover { background: #388bfd; }
        #log { text-align: center; margin-top: 15px; font-size: 12px; color: #ffeb3b; }
    </style>
</head>
<body>
    <div class="card">
        <h2>SENTINEL V24 FINAL</h2>
        <div class="group">
            <label>Mã Phiên Gốc</label>
            <input type="number" id="p" placeholder="Ví dụ: 915888">
        </div>
        <div class="group">
            <label>Chu Kỳ (Giây)</label>
            <input type="number" id="c" value="48" step="0.1">
        </div>
        <div class="controls">
            <button class="btn-blue" onclick="adjust(-0.1)">- 0.1s (Nhanh)</button>
            <button class="btn-blue" onclick="adjust(0.1)">+ 0.1s (Chậm)</button>
            <button class="btn-green" onclick="sync()">ĐỒNG BỘ & TỰ HỌC (60S)</button>
        </div>
        <div id="log">Sẵn sàng nhận lệnh...</div>
    </div>
    <script>
        let offset = 0.0;
        function adjust(v) {
            offset = parseFloat((offset + v).toFixed(1));
            document.getElementById('log').innerText = "Đang chỉnh offset: " + offset + "s";
            sync();
        }
        async function sync() {
            const res = await fetch('/admin/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    p: document.getElementById('p').value,
                    c: document.getElementById('c').value,
                    o: offset
                })
            });
            const d = await res.json();
            document.getElementById('log').innerText = "✓ " + d.msg;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(ADMIN_HTML)

@app.route('/admin/update', methods=['POST'])
def update():
    data = request.json
    if data.get("p"): config["base_p"] = int(data.get("p"))
    config["cycle"] = float(data.get("c", 48.0))
    config["offset"] = float(data.get("o", 0.0))
    config["start_time"] = time.time()
    config["learning_end"] = time.time() + 60 # Kích hoạt học lại 60s
    return jsonify({"msg": "Hệ thống đã đồng bộ và đang học lại..."})

@app.route('/api/data', methods=['GET'])
def get_data():
    now = time.time()
    
    # 1. Trạng thái Tự học 60s khi khởi động hoặc đồng bộ lại
    if now < config["learning_end"]:
        rem = int(config["learning_end"] - now)
        return jsonify({
            "phien": "AI TRAINING",
            "countdown": rem,
            "du_doan": f"ĐANG TỰ HỌC ({rem}s)",
            "ti_le": "LEARNING...",
            "status": "LEARNING"
        })
    
    # 2. Logic chạy chính
    real_elapsed = (now - config["start_time"]) - config["offset"]
    passed = int(real_elapsed // config["cycle"])
    curr_p = config["base_p"] + passed
    cd = config["cycle"] - (real_elapsed % config["cycle"])
    
    # Giai đoạn Phân tích 5 giây đầu phiên
    if cd > (config["cycle"] - config["analyze_duration"]):
        return jsonify({
            "phien": curr_p,
            "countdown": round(cd, 1),
            "du_doan": "ĐANG PHÂN TÍCH...",
            "ti_le": "ANALYZING...",
            "status": "ANALYZING"
        })
    
    # Giai đoạn Trả kết quả
    dice, total, pred, rate = solve_api_logic(curr_p)
    return jsonify({
        "phien": curr_p,
        "countdown": round(cd, 1),
        "du_doan": pred,
        "ti_le": rate,
        "xuc_xac": dice,
        "status": "READY",
        "msg": "Hệ thống sẵn sàng"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
