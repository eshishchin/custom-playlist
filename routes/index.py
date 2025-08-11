from flask import Blueprint, request, render_template_string
from collections import defaultdict
import os, shutil
from config import FOOD_KEYWORDS, LINERS, BASE_INDEX
import config

index_bp = Blueprint('index', __name__)

LAST_SAVED_PATH = None

UPLOAD_TEMPLATE = """
<h2>Загрузка рекламного плейлиста</h2>
<form method=\"post\" enctype=\"multipart/form-data\">
    <label>Ключевые слова (отметьте нужные):</label><br>
    {% for word in food_keywords %}
    <input type=\"checkbox\" name=\"food_keywords\" value=\"{{ word }}\"> {{ word }}<br>
    {% endfor %}<br>
    <label>Файл плейлиста:</label><br>
    <input type=\"file\" name=\"playlist\"><br><br>
    <input type=\"submit\" value=\"Обработать\">
</form>
<p><a href=\"/generate-north\">Собрать плейлист для Бельц</a></p>
"""

RESULT_TEMPLATE = """
<h2>Обработанные блоки:</h2>
{% for time, paths in blocks.items() %}
  <b>{{ time }}</b><br>
  <ul>
    {% for path in paths %}
      <li>{{ path }}</li>
    {% endfor %}
  </ul>
{% endfor %}
<a href=\"/\">Назад</a> | <a href=\"/upload-to-air\">Загрузить на эфир</a>
"""

@index_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_keywords = request.form.getlist('food_keywords')
        file = request.files['playlist']
        filename = os.path.basename(file.filename)
        filepath = os.path.join("uploaded", filename)
        backup_path = filepath + ".bak"

        os.makedirs("uploaded", exist_ok=True)
        file.save(filepath)
        shutil.copy(filepath, backup_path)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='cp1251') as f:
                lines = f.read().splitlines()

        blocks = defaultdict(list)
        for line in lines:
            parts = line.split('\t')
            if len(parts) != 2:
                continue
            time, path = parts
            blocks[time].append(path.strip('"'))

        processed_blocks = {}
        for idx, (time, paths) in enumerate(blocks.items()):
            is_food = any(
                word.lower() in path.lower()
                for path in paths
                for word in selected_keywords
            )
            if is_food and LINERS:
                for i in reversed(range(len(paths))):
                    if 'zakr_00_737-446.mp3' in paths[i]:
                        liner_filename = LINERS[(BASE_INDEX + idx) % len(LINERS)]
                        full_liner_path = f"Реклама*Roliki\\{liner_filename}"
                        paths.insert(i, full_liner_path)
                        break
            processed_blocks[time] = paths

        with open(filepath, 'wb') as f:
            for time, paths in processed_blocks.items():
                for path in paths:
                    f.write(f"{time}\t\"{path}\"\r\n".encode('cp1251', errors='replace'))

        config.LAST_SAVED_PATH = filepath

        return render_template_string(RESULT_TEMPLATE, blocks=processed_blocks)

    return render_template_string(UPLOAD_TEMPLATE, food_keywords=FOOD_KEYWORDS)
