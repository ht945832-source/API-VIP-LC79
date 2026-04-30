import time
import os
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CẤU HÌNH HỆ THỐNG SIÊU CẤP ---
# Hoàng có thể thay đổi Pass Admin tại đây
ADMIN_PASSWORD = "hoangdz_vip_pro" 

system_data = {
    "history": [],          
    "base_p": 6812722,      
    "cycle": 48.0,          
    "start_time": time.time(),
    "last_update": "Chưa có dữ liệu"
}

# --- THUẬT TOÁN SOI CẦU MD5 NÂNG CAO ---
def master_analyze(history):
    if not history: return "ĐANG CHỜ CẦU", "0%"
    
    # Lấy 10 cầu gần nhất để phân tích sâu
    recent = history[-10:]
    t_count = recent.count('T')
    x_count = recent.count('X')
    
    # Ưu tiên soi bệt dài (cầu đặc trưng MD5)
    if len(history) >= 5:
        if history[-4:] == ['T']*4: return "BỆT TÀI", "98%"
        if history[-4:] == ['X']*4: return "BỆT XỈU", "98%"
        
    # Soi cầu nghiêng và hồi cầu
    if t_count > x_count:
        return "CHẮC TÀI", f"{75 + (t_count * 2)}%"
    else:
        return "CHẮC XỈU", f"{75 + (x_count * 2)}%"

# --- GIAO DIỆN ADMIN FULL QUYỀN ---
ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>QUẢN TRỊ VIÊN - HOANGDZ SENTINEL</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root { --neon: #0f0; --bg: #050505; }
        body { background: var(--bg); color: var(--neon); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 15px; }
        .container { max-width: 600px; margin: auto; border: 2px solid var(--neon); border-radius: 20px; padding: 20px; box-shadow: 0 0 20px rgba(0,255,0,0.2); }
        h1 { font-size: 20px; text-transform: uppercase; border-bottom: 1px solid var(--neon); padding-bottom: 10px; }
        .section { margin-bottom: 25px; text-align: left; }
        label { display: block; margin-bottom: 8px; font-weight: bold; font-size: 14px; }
        input, textarea { width: 100%; padding: 12px; background: #111; border: 1px solid #333; color: var(--neon); border-radius: 10px; margin-bottom: 10px; box-sizing: border-box; }
        input:focus, textarea:focus { border-color: var(--neon); outline: none; box-shadow: 0 0 10px var(--neon); }
        button { width: 100%; padding: 15px; background: var(--neon); color: #000; border: none; border-radius: 30px; font-weight: bold; cursor: pointer; transition: 0.3s; margin-top: 5px; }
        button:active { transform: scale(0.95); }
        .status-bar { font-size: 12px; color: #fff; background: #222; padding: 10px; border-radius: 5px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ ADMIN CONTROL FULL ACCESS</h1>
        
        <div class="section">
            <label>🔑 MẬT KHẨU ADMIN:</label>
            <input type="password" id="pass" placeholder="Nhập pass để thực thi lệnh">
        </div>

        <div class="section">
            <label>⏱️ CÀI ĐẶT THỜI GIAN & PHIÊN:</label>
            <input type="number" id="p" placeholder="Phiên hiện tại (VD: 6812722)">
            <input type="number" id="s" placeholder="Số giây mỗi phiên (Mặc định: 48)">
            <button onclick="saveTime()">ĐỒNG BỘ NGAY</button>
        </div>

        <div class="section">
            <label>📊 NHẬP CẦU HÀNG LOẠT (TỰ DO):</label>
            <textarea id="list" rows="5" placeholder="Dán cực nhiều cầu vào đây, ngăn cách bằng dấu phẩy. VD: T,X,T,T,X,X,T,T,T,X..."></textarea>
            <button onclick="saveCau()">CẬP NHẬT DATABASE CẦU</button>
            <button onclick="clearAll()" style="background:#ff0000; color:#fff; margin-top:10px;">RESET TOÀN BỘ DATA</button>
        </div>

        <div class="status-bar" id="stat">Trạng thái: Sẵn sàng</div>
    </div>

    <script>
        async function callAPI(path, body) {
            const pass = document.getElementById('pass').value;
            if(!pass) return alert("Vui lòng nhập mật khẩu Admin!");
            
            const res = await fetch(path, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({...body, pass})
            });
            const data = await res.json();
            if(data.error) alert("LỖI: " + data.error);
            else {
                document.getElementById('stat').innerText = "Cập nhật lúc: " + new Date().toLocaleTimeString();
                alert(data.msg);
            }
        }

        function saveTime() {
            const p = document.getElementById('p').value;
            const s = document.getElementById('s').value;
            callAPI('/admin/sync', {p, s});
        }

        function saveCau() {
            const val = document.getElementById('list').value;
            callAPI('/admin/history', {val});
        }

        function clearAll() {
            callAPI('/admin/clear', {});
        }
    </script>
</body>
</html>
'''

# --- XỬ LÝ LOGIC SERVER ---

@app.route('/admin')
def admin_panel():
    return render_template_string(ADMIN_TEMPLATE)

@app.route('/admin/sync', methods=['POST'])
def sync_data():
    r = request.json
    if r.get('pass') != ADMIN_PASSWORD: return jsonify({"error": "Sai mật khẩu!"}), 403
    
    if r.get('p'): system_data["base_p"] = int(r.get('p'))
    if r.get('s'): system_data["cycle"] = float(r.get('s'))
    system_data["start_time"] = time.time()
    return jsonify({"msg": "Đã đồng bộ phiên và thời gian thành công!"})

@app.route('/admin/history', methods=['POST'])
def set_history():
    r = request.json
    if r.get('pass') != ADMIN_PASSWORD: return jsonify({"error": "Sai mật khẩu!"}), 403
    
    raw_val = r.get('val', '')
    # Tự động lọc và làm sạch dữ liệu: Chỉ lấy T và X[span_1](start_span)[span_1](end_span)
    cleaned = [x.strip().upper() for x in raw_val.split(',') if x.strip().upper() in ['T', 'X']]
    system_data["history"] = cleaned
    return jsonify({"msg": f"Đã nạp thành công {len(cleaned)} cầu vào hệ thống!"})

@app.route('/admin/clear', methods=['POST'])
def clear_data():
    r = request.json
    if r.get('pass') != ADMIN_PASSWORD: return jsonify({"error": "Sai mật khẩu!"}), 403
    system_data["history"] = []
    return jsonify({"msg": "Đã xoá sạch dữ liệu!"})

@app.route('/api/data', methods=['GET'])
def get_public_data():
    elapsed = time.time() - system_data["start_time"]
    passed = int(elapsed // system_data["cycle"])
    
    curr_p = system_data["base_p"] + passed
    countdown = int(system_data["cycle"] - (elapsed % system_data["cycle"]))
    
    pred, rate = master_analyze(system_data["history"])
    
    return jsonify({
        "phien": curr_p,
        "countdown": countdown,
        "du_doan": pred,
        "ti_le": rate,
        "history_count": len(system_data["history"])
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
