from .index import index_bp
from .upload_to_air import upload_bp
from .generate_north import north_bp

def register_routes(app):
    app.register_blueprint(index_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(north_bp)
