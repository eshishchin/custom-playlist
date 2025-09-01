# routes/upload_to_air.py
from flask import Blueprint, redirect, url_for
import config, os, shutil
from utils_last import get_last_saved_path

upload_bp = Blueprint('upload_to_air', __name__)

@upload_bp.route('/upload-to-air')
def upload_to_air():
    path = get_last_saved_path()
    if path and os.path.exists(path):
        dest_path = os.path.join("/mnt/synadyn/!Playlist/Reclama/", os.path.basename(path))
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy(path, dest_path)
        # редирект с сообщением для модалки
        return redirect(url_for('index.index', uploaded='1', dest=dest_path))
    return redirect(url_for('index.index', error="Файл не найден. Сначала загрузите и обработайте плейлист."))
