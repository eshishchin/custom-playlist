from flask import Blueprint, request, render_template
import os
from collections import defaultdict
import random

north_bp = Blueprint('generate_north', __name__)

import config

@north_bp.route('/generate-north', methods=['GET', 'POST'])
def generate_north():
    if not config.LAST_SAVED_PATH or not os.path.exists(config.LAST_SAVED_PATH):
        return "<p>Сначала загрузите и обработайте основной плейлист.</p><a href='/'>Назад</a>"

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

        try:
            with open(config.LAST_SAVED_PATH, 'r', encoding='cp1251') as f:
                lines = f.read().splitlines()
        except:
            return "<p>Ошибка при чтении оригинального файла.</p><a href='/'>Назад</a>"

        blocks = defaultdict(list)
        for line in lines:
            parts = line.split('\t')
            if len(parts) != 2:
                continue
            t, pth = parts
            blocks[t].append(pth.strip('"'))

        # Применение _DTMF для нужных временных блоков
        all_keys = set(insert_map.keys()) | set(delete_map.keys()) | liner_map
        for time_key in all_keys:
            if time_key in blocks:
                for i in range(len(blocks[time_key])):
                    line = blocks[time_key][i]
                    if 'РЕКЛАМА' in line or 'zakr_00_737-446' in line.lower():
                        blocks[time_key][i] = line.replace('.mp3', '_DTMF.mp3')

        # Сохраняем основной файл с _DTMF
        main_path = os.path.join("/mnt/synadyn/!Playlist/Reclama/", os.path.basename(config.LAST_SAVED_PATH))
        os.makedirs(os.path.dirname(main_path), exist_ok=True)
        with open(main_path, 'wb') as f:
            for time, paths in blocks.items():
                for path in paths:
                    f.write(f"{time}\t\"{path}\"\r\n".encode('cp1251', errors='replace'))

        # Генерация северного плейлиста
        sever_blocks = {}
        for full_time, inserts in insert_map.items():
            if full_time not in blocks:
                continue

            block = blocks[full_time][:]

            # Удаление по delete_map и _id
            block = [line for line in block if not any(
                kw in line.lower() for kw in delete_map.get(full_time, [])
            ) and '_id' not in line.lower()]

            # Вставка лайнера перед zakr
            if full_time in liner_map and config.LINERS:
                for i in reversed(range(len(block))):
                    if 'zakr_00_737-446' in block[i].lower():
                        liner = random.choice(config.LINERS)
                        block.insert(i, f"Реклама*Roliki\\{liner}")
                        break

            # Вставка новых файлов после РЕКЛАМА
            insert_paths = [f"Реклама*Roliki_B\\{f}" for f in inserts]
            insert_position = next((i + 1 for i, line in enumerate(block) if 'реклама' in line.lower()), len(block))
            block[insert_position:insert_position] = insert_paths

            # Добивка после каждой zakr
            i = 0
            while i < len(block):
                if 'zakr_00_737-446' in block[i].lower():
                    block.insert(i + 1, 'Реклама*Decro\\Sweeps\\WHITE NOISE 02.mp3')
                    i += 1  # пропустить добивку
                i += 1

            sever_blocks[full_time] = block

        # Убираем _DTMF из северного плейлиста
        for time_key in sever_blocks:
            for i in range(len(sever_blocks[time_key])):
                sever_blocks[time_key][i] = sever_blocks[time_key][i].replace('_DTMF.mp3', '.mp3')

        # Сохраняем северный файл
        sever_path = os.path.join("/mnt/synadyn/!Playlist/Reclama/Sever/", os.path.basename(config.LAST_SAVED_PATH))
        os.makedirs(os.path.dirname(sever_path), exist_ok=True)
        with open(sever_path, 'wb') as f:
            for time, paths in sever_blocks.items():
                for path in paths:
                    f.write(f"{time}\t\"{path}\"\r\n".encode('cp1251', errors='replace'))

        return f"<p>Северный плейлист сохранён: {sever_path}</p><a href='/'>Назад</a>"

    return render_template("generate_north.html")
