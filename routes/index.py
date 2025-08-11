# routes/index.py
from flask import Blueprint, request, render_template, redirect, url_for
from collections import defaultdict, OrderedDict
from werkzeug.utils import secure_filename
from config import FOOD_KEYWORDS, LINERS, BASE_INDEX, UPLOAD_DIR
import config, os, shutil, json

index_bp = Blueprint('index', __name__)

@index_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_keywords = request.form.getlist('food_keywords')
        file = request.files.get('playlist')

        if not file or file.filename == '':
            return render_template('upload.html', food_keywords=FOOD_KEYWORDS, error="Файл не выбран")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = secure_filename(os.path.basename(file.filename))
        filepath = UPLOAD_DIR / filename
        backup_path = filepath.with_suffix(filepath.suffix + ".bak")

        file.save(str(filepath))
        shutil.copy(str(filepath), str(backup_path))

        # чтение с fallback
        for enc in ('utf-8', 'cp1251'):
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    lines = f.read().splitlines()
                break
            except UnicodeDecodeError:
                continue

        blocks = defaultdict(list)
        for line in lines:
            parts = line.split('\t')
            if len(parts) != 2:
                continue
            time, path = parts
            blocks[time].append(path.strip('"'))

        processed = OrderedDict()
        for idx, time in enumerate(sorted(blocks.keys())):
            paths = blocks[time]
            is_food = any(w.lower() in p.lower() for p in paths for w in selected_keywords)
            if is_food and LINERS:
                for i in reversed(range(len(paths))):
                    low = paths[i].lower()
                    if 'zakr_00_737-446.mp3' in low or 'zakr_737-446' in low:
                        liner = LINERS[(BASE_INDEX + idx) % len(LINERS)]
                        paths.insert(i, f"Реклама*Roliki\\{liner}")
                        break
            processed[time] = paths

        with open(filepath, 'wb') as out:
            for t, arr in processed.items():
                for p in arr:
                    out.write(f'{t}\t"{p}"\r\n'.encode('cp1251', errors='replace'))

        config.LAST_SAVED_PATH = str(filepath)
        try:
            config.STATE_FILE.write_text(
                json.dumps({"last_path": config.LAST_SAVED_PATH}, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception:
            pass

        # рендерим ту же страницу с модалкой результата
        return render_template('upload.html',
                               food_keywords=FOOD_KEYWORDS,
                               error=None,
                               blocks=processed,
                               just_processed=True)

    # GET
    return render_template('upload.html',
                           food_keywords=FOOD_KEYWORDS,
                           error=None,
                           blocks=None,
                           just_processed=False)
