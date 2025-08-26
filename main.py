import os
from flask import Flask
from main_routes import main_routes
from calendar_routes import calendar_routes

app = Flask(__name__)
app.register_blueprint(main_routes)
app.register_blueprint(calendar_routes)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Renderが指定するPORTを取得
    app.run(host="0.0.0.0", port=port, debug=False)
