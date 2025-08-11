from flask import Blueprint
import config
import os, shutil

upload_bp = Blueprint('upload_to_air', __name__)

@upload_bp.route('/upload-to-air')
def upload_to_air():
    path = config.LAST_SAVED_PATH

    if path and os.path.exists(path):
        dest_path = os.path.join("/mnt/synadyn/!Playlist/Reclama/", os.path.basename(path))
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy(path, dest_path)
        return f"<p>Файл загружен на эфир: {dest_path}</p><a href='/'>Назад</a>"
    return "<p>Файл не найден. Сначала загрузите и обработайте плейлист.</p><a href='/'>Назад</a>"
