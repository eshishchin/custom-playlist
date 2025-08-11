from flask import Blueprint, request
from config import LAST_SAVED_PATH
import os
from collections import defaultdict

dtmf_bp = Blueprint("dtmf", __name__)

@dtmf_bp.route("/apply-dtmf", methods=["POST"])
def apply_dtmf():
    if not LAST_SAVED_PATH or not os.path.exists(LAST_SAVED_PATH):
        return "Исходный файл не найден"

    raw_times = request.form.get("dtmf_times", "")
    full_times = [line.strip() for line in raw_times.splitlines() if line.strip()]
    times_only = [ft.split()[1] for ft in full_times if ' ' in ft]

    try:
        with open(LAST_SAVED_PATH, 'r', encoding='cp1251') as f:
            lines = f.read().splitlines()
    except Exception as e:
        return f"Ошибка чтения файла: {e}"

    blocks = defaultdict(list)
    for line in lines:
        if '\t' in line:
            time, path = line.split('\t')
            blocks[time].append(path.strip('"'))

    for time in times_only:
        if time not in blocks:
            continue
        block = blocks[time]
        for i in range(len(block)):
            if 'РЕКЛАМА' in block[i] or 'zakr_737-446' in block[i]:
                block[i] = block[i].replace('.mp3', '_DTMF.mp3')

    base_name = os.path.basename(LAST_SAVED_PATH)
    chisinau_path = os.path.join("/mnt/synadyn/!Playlist/Reclama")

    os.makedirs(os.path.dirname(chisinau_path), exist_ok=True)
    with open(chisinau_path, 'wb') as f:
        for time, paths in blocks.items():
            for path in paths:
                line = f"{time}\t\"{path}\"\r\n"
                f.write(line.encode('cp1251', errors='replace'))

    return f"Файл для Кишинёва сохранён: {chisinau_path}"
