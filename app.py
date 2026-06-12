from flask import Flask
from config import SECRET_KEY, HOST, PORT, DEBUG
from database.db import init_database
from routes.routes import main
 
app = Flask(__name__)
app.secret_key = SECRET_KEY
 
app.register_blueprint(main)
 
# Appelé au démarrage, que ce soit via gunicorn ou python app.py
init_database()
 
if __name__ == "__main__":
    print("=" * 60)
    print("  SDEL Inventory — Système de Gestion des Stocks")
    print("=" * 60)
    print(f"  Serveur démarré sur http://{HOST}:{PORT}")
    print("=" * 60)
    app.run(host=HOST, port=PORT, debug=DEBUG)
