from flask import Flask
from main_routes import main_routes
from calendar_routes import calendar_routes

app = Flask(__name__)
app.register_blueprint(main_routes)
app.register_blueprint(calendar_routes)

if __name__ == '__main__':
    app.run(debug=True)
