import os
from flask import Flask, request, jsonify
from threading import Thread

app = Flask(__name__)

_bot_ref = None

def set_bot(bot):
    global _bot_ref
    _bot_ref = bot

@app.route('/')
def home():
    return "O Império de Tenshi está de pé. 👁️"

@app.route('/status')
def status():
    if _bot_ref is None:
        return jsonify({"online": False, "guilds": 0, "latency": 0, "user": None})
    try:
        ready = _bot_ref.is_ready()
        guilds = len(_bot_ref.guilds) if ready else 0
        latency = round(_bot_ref.latency * 1000, 1) if ready else 0
        user = str(_bot_ref.user) if _bot_ref.user else None
        return jsonify({"online": ready, "guilds": guilds, "latency": latency, "user": user})
    except Exception as e:
        return jsonify({"online": False, "guilds": 0, "latency": 0, "user": None, "error": str(e)})

@app.route('/reconnect', methods=['POST'])
def reconnect():
    secret = os.environ.get("ADMIN_SECRET", "")
    token = request.headers.get("X-Admin-Token", "")
    if not secret or token != secret[:32]:
        return jsonify({"error": "Unauthorized"}), 401
    if _bot_ref is None:
        return jsonify({"error": "Bot não iniciado"}), 503
    try:
        import asyncio
        loop = _bot_ref.loop
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(_bot_ref.close(), loop)
        return jsonify({"ok": True, "message": "Bot encerrando — Replit vai reiniciar automaticamente."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run():
    port = int(os.environ.get("PORT", 8090))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
