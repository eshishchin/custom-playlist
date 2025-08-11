from flask import Flask
from routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile("config.py")
    register_routes(app)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=8081)
