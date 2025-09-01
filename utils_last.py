# utils_last.py
import os, json
from pathlib import Path
import config

def get_last_saved_path() -> str | None:
    """Пытается вернуть актуальный путь к последнему обработанному плейлисту.
    Порядок: память -> STATE_FILE -> самый свежий uploaded/*.txt
    """
    p = config.LAST_SAVED_PATH
    if p and os.path.exists(p):
        return p

    try:
        if config.STATE_FILE.exists():
            data = json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
            p = data.get("last_path")
            if p and os.path.exists(p):
                config.LAST_SAVED_PATH = p
                return p
    except Exception:
        pass

    try:
        files = sorted(
            Path(config.UPLOAD_DIR).glob("*.txt"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        if files:
            p = str(files[0])
            config.LAST_SAVED_PATH = p
            return p
    except Exception:
        pass

    return None

def set_last_saved_path(p: str) -> None:
    """Атомарно сохраняет путь и прогревает память текущего процесса."""
    try:
        tmp = config.STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps({"last_path": p}, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, config.STATE_FILE)  # атомарная замена
    except Exception:
        pass
    config.LAST_SAVED_PATH = p