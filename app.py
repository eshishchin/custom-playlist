from flask import Flask
from routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile("config.py")
    register_routes(app)

    try:
        if config.STATE_FILE.exists():
            data = json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
            p = data.get("last_path")
            if p:
                config.LAST_SAVED_PATH = p
    except Exception:
        pass

    return app

app = create_app()

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=8081)
