# routes/generate_south.py
from flask import Blueprint, request, render_template
import os
from collections import defaultdict
from datetime import datetime
import config
from utils_last import get_last_saved_path

south_bp = Blueprint('generate_south', __name__)

def get_date_from_filename(path: str) -> str:
    base = os.path.basename(path)
    name, _ = os.path.splitext(base)
    try:
        return datetime.strptime(name, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return ""

@south_bp.route('/generate-south', methods=['GET', 'POST'])
def generate_south():
    path = get_last_saved_path()
    date_ymd = get_date_from_filename(path) if path else ""

    if not path or not os.path.exists(path):
        return render_template("generate_north.html",  # используем тот же шаблон
                               date_ymd=date_ymd, success_path=None, need_upload=True)

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
            # добавим .mp3 если не указано
            def ensure_mp3(n: str):
                n = n.strip().strip('"').strip("'")
                return n if (n and n.lower().endswith('.mp3')) else (n + '.mp3' if n else '')
            insert_map[key] = [ensure_mp3(x) for x in ins.split(',') if ensure_mp3(x)]
            delete_map[key] = [x.strip().lower() for x in dels.split(',') if x.strip()]
            if lin.strip().lower() == 'yes':
                liner_map.add(key)

        # читаем основной
        with open(path, 'r', encoding='cp1251') as f:
            lines = f.read().splitlines()

        blocks = defaultdict(list)
        for line in lines:
            parts = line.split('\t')
            if len(parts) != 2:
                continue
            t, pth = parts
            blocks[t].append(pth.strip('"'))

        # Применяем _DTMF в отмеченных блоках (как в north)
        all_keys = set(insert_map.keys()) | set(delete_map.keys()) | liner_map
        for time_key in all_keys:
            if time_key in blocks:
                for i, line in enumerate(blocks[time_key]):
                    ll = line
                    if ('РЕКЛАМА' in ll) or ('zakr_00_737-446' in ll) or ('zakr_737-446' in ll):
                        if not line.endswith('_DTMF.mp3'):
                            if line.lower().endswith('.mp3'):
                                blocks[time_key][i] = line[:-4] + '_DTMF.mp3'

        # Сохраняем «Кишинёв» (основной) на место
        main_path = os.path.join("/mnt/synadyn/!Playlist/Reclama/", os.path.basename(path))
        os.makedirs(os.path.dirname(main_path), exist_ok=True)
        with open(main_path, 'wb') as f:
            for t in sorted(blocks.keys()):
                for p in blocks[t]:
                    f.write(f'{t}\t"{p}"\r\n'.encode('cp1251', errors='replace'))

        # Собираем ЮГ
        south_blocks = {}
        for full_time, inserts in insert_map.items():
            if full_time not in blocks:
                continue
            block = blocks[full_time][:]

            # delete + _id
            block = [
                line for line in block
                if not any(kw in line.lower() for kw in delete_map.get(full_time, []))
                and '_id' not in line.lower()
            ]

            # лайнер перед zakr — как в north
            if full_time in liner_map and config.LINERS:
                for i in reversed(range(len(block))):
                    if 'zakr_00_737-446' in block[i].lower() or 'zakr_737-446' in block[i].lower():
                        liner = config.LINERS[(config.BASE_INDEX + hash(full_time)) % len(config.LINERS)]
                        block.insert(i, f'Реклама*Roliki\\{liner}')
                        break

            # вставки: для Юга меняем пул на Roliki_U
            insert_paths = [f'Реклама*Roliki_U\\{f}' for f in inserts]
            insert_position = next((i + 1 for i, line in enumerate(block) if 'реклама' in line.lower()), len(block))
            block[insert_position:insert_position] = insert_paths

            # WHITE NOISE после каждого zakr
            i = 0
            while i < len(block):
                if 'zakr_00_737-446' in block[i].lower() or 'zakr_737-446' in block[i].lower():
                    if i+1 >= len(block) or 'white noise 02.mp3' not in block[i+1].lower():
                        block.insert(i + 1, 'Реклама*Decro\\Sweeps\\WHITE NOISE 02.mp3')
                        i += 1
                i += 1

            # в региональном плейлисте убираем _DTMF
            block = [b.replace('_DTMF.mp3', '.mp3') for b in block]
            south_blocks[full_time] = block

        south_path = os.path.join("/mnt/synadyn/!Playlist/Reclama/Ug/",
                                  os.path.basename(path))
        os.makedirs(os.path.dirname(south_path), exist_ok=True)
        with open(south_path, 'wb') as f:
            for t in sorted(south_blocks.keys()):
                for p in south_blocks[t]:
                    f.write(f'{t}\t"{p}"\r\n'.encode('cp1251', errors='replace'))

        return render_template("generate_north.html",  # используем общий UI
                               date_ymd=date_ymd,
                               need_upload=False,
                               success_path=south_path)

    # GET
    return render_template("generate_north.html",
                           date_ymd=date_ymd,
                           need_upload=False,
                           success_path=None)