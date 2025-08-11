# routes/generate_north.py
from flask import Blueprint, request, render_template
import os, json
from collections import defaultdict, OrderedDict
import random
import config
from datetime import datetime

north_bp = Blueprint('generate_north', __name__)

def get_date_from_filename():
    """Возвращает YYYY-MM-DD из имени последнего файла, либо ''."""
    path = config.LAST_SAVED_PATH
    if not path or not os.path.exists(path):
        # пробуем state
        try:
            if config.STATE_FILE.exists():
                data = json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
                path = data.get("last_path")
        except Exception:
            pass
    if not path:
        return ''
    base = os.path.basename(path)  # например 2025-08-11.txt
    name, _ = os.path.splitext(base)
    # в имени ожидаем YYYY-MM-DD
    try:
        dt = datetime.strptime(name, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return ''

@north_bp.route('/generate-north', methods=['GET', 'POST'])
def generate_north():
    date_ymd = get_date_from_filename()
    # если совсем нет файла — просим загрузить
    if not config.LAST_SAVED_PATH or not os.path.exists(config.LAST_SAVED_PATH):
        return render_template("generate_north.html", date_ymd=date_ymd, success_path=None, need_upload=True)

    if request.method == 'POST':
        data = request.form.get('rows', '')
        rows = data.splitlines() if data else []

        insert_map, delete_map, liner_map = {}, {}, set()
        for row in rows:
            parts = row.split('|')
            if len(parts) != 4:
                continue
            dt, ins, dels, lin = parts
            key = dt.strip()
            insert_map[key] = [x.strip() for x in ins.split(',') if x.strip()]
            delete_map[key] = [x.strip().lower() for x in dels.split(',') if x.strip()]
            if lin.strip().lower() == 'yes':
                liner_map.add(key)

        # читаем основной
        try:
            with open(config.LAST_SAVED_PATH, 'r', encoding='cp1251') as f:
                lines = f.read().splitlines()
        except:
            return render_template("generate_north.html", date_ymd=date_ymd, success_path=None, need_upload=True)

        blocks = defaultdict(list)
        for line in lines:
            parts = line.split('\t')
            if len(parts) != 2:
                continue
            t, pth = parts
            blocks[t].append(pth.strip('"'))

        # применяем _DTMF
        all_keys = set(insert_map.keys()) | set(delete_map.keys()) | liner_map
        for time_key in all_keys:
            if time_key in blocks:
                for i, line in enumerate(blocks[time_key]):
                    ll = line()
                    if ('РЕКЛАМА' in ll) or ('zakr_00_737-446' in ll) or ('zakr_737-446' in ll):
                        if not ll.endswith('_dtmf.mp3'):
                            blocks[time_key][i] = line.replace('.mp3', '_DTMF.mp3')

        # сохраняем основной файл
        main_path = os.path.join("/mnt/synadyn/!Playlist/Reclama/", os.path.basename(config.LAST_SAVED_PATH))
        os.makedirs(os.path.dirname(main_path), exist_ok=True)
        with open(main_path, 'wb') as f:
            for time in sorted(blocks.keys()):
                for path in blocks[time]:
                    f.write(f"{time}\t\"{path}\"\r\n".encode('cp1251', errors='replace'))

        # собираем север
        sever_blocks = {}
        for full_time, inserts in insert_map.items():
            if full_time not in blocks:
                continue
            block = blocks[full_time][:]

            block = [line for line in block
                     if not any(kw in line.lower() for kw in delete_map.get(full_time, []))
                     and '_id' not in line.lower()]

            if full_time in liner_map and config.LINERS:
                for i in reversed(range(len(block))):
                    if 'zakr_00_737-446' in block[i].lower() or 'zakr_737-446' in block[i].lower():
                        liner = config.LINERS[(config.BASE_INDEX + hash(full_time)) % len(config.LINERS)]
                        block.insert(i, f"Реклама*Roliki\\{liner}")
                        break

            insert_paths = [f"Реклама*Roliki_B\\{f}" for f in inserts]
            insert_position = next((i + 1 for i, line in enumerate(block) if 'реклама' in line.lower()), len(block))
            block[insert_position:insert_position] = insert_paths

            i = 0
            while i < len(block):
                if 'zakr_00_737-446' in block[i].lower() or 'zakr_737-446' in block[i].lower():
                    if i+1 >= len(block) or 'white noise 02.mp3' not in block[i+1].lower():
                        block.insert(i + 1, 'Реклама*Decro\\Sweeps\\WHITE NOISE 02.mp3')
                        i += 1
                i += 1

            block = [b.replace('_DTMF.mp3', '.mp3') for b in block]
            sever_blocks[full_time] = block

        sever_path = os.path.join("/mnt/synadyn/!Playlist/Reclama/Sever/",
                                  os.path.basename(config.LAST_SAVED_PATH))
        os.makedirs(os.path.dirname(sever_path), exist_ok=True)
        with open(sever_path, 'wb') as f:
            for time in sorted(sever_blocks.keys()):
                for path in sever_blocks[time]:
                    f.write(f"{time}\t\"{path}\"\r\n".encode('cp1251', errors='replace'))

        # Рендерим ту же страницу, но с модалкой успеха
        return render_template("generate_north.html",
                               date_ymd=date_ymd,
                               need_upload=False,
                               success_path=sever_path)

    # GET
    return render_template("generate_north.html",
                           date_ymd=date_ymd,
                           need_upload=False,
                           success_path=None)
