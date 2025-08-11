from flask import Blueprint, request
from config import LAST_SAVED_PATH, AIR_DIR
import os
from collections import defaultdict
from pathlib import Path

dtmf_bp = Blueprint("dtmf", __name__)

@dtmf_bp.route("/apply-dtmf", methods=["POST"])
def apply_dtmf():
    if not LAST_SAVED_PATH or not os.path.exists(LAST_SAVED_PATH):
        return "Исходный файл не найден"

    raw_times = request.form.get("dtmf_times", "")
    full_times = [line.strip() for line in raw_times.splitlines() if line.strip()]
    times_only = []
    for ft in full_times:
        parts = ft.split()
        if len(parts) >= 2:
            times_only.append(parts[1])

    try:
        with open(LAST_SAVED_PATH, 'r', encoding='cp1251') as f:
            lines = f.read().splitlines()
    except Exception as e:
        return f"Ошибка чтения файла: {e}"

    blocks = defaultdict(list)
    for line in lines:
        if '\t' in line:
            time, path = line.split('\t', 1)
            blocks[time].append(path.strip('"'))

    times_set = set(times_only)
    for time, arr in blocks.items():
        if time not in times_set:
            continue
        for i, p in enumerate(arr):
            pl = p.lower()
            if ('реклама' in pl) or ('zakr_737-446' in pl) or ('zakr_00_737-446' in pl):
                if not pl.endswith('_dtmf.mp3'):
                    arr[i] = p.replace('.mp3', '_DTMF.mp3')

    src_name = os.path.basename(LAST_SAVED_PATH)
    dest_file = AIR_DIR / src_name
    os.makedirs(dest_file.parent, exist_ok=True)
    with open(dest_file, 'wb') as f:
        for time in sorted(blocks.keys()):
            for path in blocks[time]:
                f.write(f"{time}\t\"{path}\"\r\n".encode('cp1251', errors='replace'))

    return f"Файл для Кишинёва сохранён: {dest_file}"
