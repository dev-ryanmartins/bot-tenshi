from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "O Império de Tenshi está de pé. 👁️"

def run():
    app.run(host='0.0.0.0', port=8090)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
