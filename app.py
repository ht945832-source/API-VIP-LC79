import time
import os
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- DATABASE TẠM THỜI ---
system_data = {
    "history": [],          # Danh sách cầu Hoàng nhập (T hoặc X)
    "base_p": 915800,
    "cycle": 48.0,
    "start_time": time.time(),
    "last_pred": "ĐANG CHỜ CẦU"
}

# --- THUẬT TOÁN PHÂN TÍCH CẦU THỰC TẾ ---
def analyze_patterns(history):
    if not history: return "CHỜ CẦU", "0%"
    
    # Lấy 5 phiên gần nhất để soi
    last_5 = history[-5:]
    count_t = last_5.count('T')
    count_x = last_5.count('X')
    
    # Logic soi cầu cơ bản
    if len(history) >= 3:
        # Soi cầu bệt
        if last_5[-3:] == ['T', 'T', 'T']: return "CHẮC TÀI", "89%"
        if last_5[-3:] == ['X', 'X', 'X']: return "CHẮC XỈU", "89%"
        # Soi cầu 1-1
        if last_5[-2:] == ['T', 'X']: return "CHẮC TÀI", "82%"
        if last_5[-2:] == ['X', 'T']: return "CHẮC XỈU", "82%"

    # Soi cầu nghiêng
    if count_t > count_x: return "CHẮC TÀI", f"{70 + count_t*3}%"
    return "CHẮC XỈU", f"{70 + count_x*3}%"

# --- GIAO DIỆN ADMIN CÓ NHẬP CẦU ---
ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>HOANGDZ - PATTERN ADMIN</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #0a0a0a; color: #0f0; font-family: sans-serif; text-align: center; }
        .box { border: 1px solid #0f0; padding: 20px; margin: 10px; border-radius: 15px; }
        input, button { padding: 10px; margin: 5px; border-radius: 5px; border: 1px solid #0f0; background: #000; color: #0f0; }
        .history-list { font-size: 20px; letter-spacing: 5px; color: #fff; }
    </style>
</head>
<body>
    <div class="box">
        <h2>NHẬP CẦU THỰC TẾ</h2>
        <p>Gõ T (Tài) hoặc X (Xỉu) vừa ra:</p>
        <input type="text" id="cau" placeholder="Ví dụ: T" maxlength="1">
        <button onclick="add()">THÊM CẦU</button>
        <button onclick="clearCau()" style="color: red;">XOÁ HẾT</button>
        <div class="history-list" id="list"></div>
    </div>
    
    <div class="box">
        <h3>ĐỒNG BỘ PHIÊN</h3>
        <input type="number" id="p" placeholder="Số phiên hiện tại">
        <button onclick="syncP()">ĐỒNG BỘ</button>
    </div>

    <script>
        async function add() {
            const val = document.getElementById('cau').value.toUpperCase();
            if(val !== 'T' && val !== 'X') return alert("Chỉ nhập T hoặc X");
            await fetch('/admin/add-cau', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({val})
            });
            document.getElementById('cau').value = '';
            load();
        }
        async function clearCau() {
            await fetch('/admin/clear', {method: 'POST'});
            load();
        }
        async function syncP() {
            const p = document.getElementById('p').value;
            await fetch('/admin/sync', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({p})
            });
            alert("Đã đồng bộ phiên!");
        }
        async function load() {
            const res = await fetch('/api/data');
            const data = await res.json();
            document.getElementById('list').innerText = data.history.join(' - ');
        }
        setInterval(load, 2000);
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(ADMIN_HTML)

@app.route('/admin/add-cau', methods=['POST'])
def add_cau():
    val = request.json.get('val')
    system_data["history"].append(val)
    if len(system_data["history"]) > 20: system_data["history"].pop(0)
    return jsonify({"status": "ok"})

@app.route('/admin/clear', methods=['POST'])
def clear_cau():
    system_data["history"] = []
    return jsonify({"status": "ok"})

@app.route('/admin/sync', methods=['POST'])
def sync_p():
    p = request.json.get('p')
    if p: system_data["base_p"] = int(p)
    system_data["start_time"] = time.time()
    return jsonify({"status": "ok"})

@app.route('/api/data', methods=['GET'])
def get_api():
    now = time.time()
    elapsed = now - system_data["start_time"]
    passed = int(elapsed // system_data["cycle"])
    curr_p = system_data["base_p"] + passed
    countdown = int(system_data["cycle"] - (elapsed % system_data["cycle"]))
    
    pred, rate = analyze_patterns(system_data["history"])
    
    return jsonify({
        "phien": curr_p,
        "countdown": countdown,
        "du_doan": pred,
        "ti_le": rate,
        "history": system_data["history"],
        "status": "LIVE" if countdown < 43 else "ANALYZING"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
