import datetime
from pathlib import Path

# Ключевые слова, связанные с едой и брендами
FOOD_KEYWORDS = [
    "Kauf",
    "Local",
    "Kfc",
    "Linella",
    "Mezellini",
    "Nivalli",
    "Rogob",
    "Slav"
]

# Фиксированный список лайнеров
LINERS = [
    "CCA-sare.wav",
    "CCA-mesele.wav",
    "CCA-5fructe.wav",
    "CCA-30min.wav",
    "CCA-2litri.wav"
]

# Базовая дата для индекса
BASE_INDEX = datetime.date.today().toordinal()

# Директории

UPLOAD_DIR = Path("uploaded")
AIR_DIR = Path("/mnt/synadyn/!Playlist/Reclama")
NORTH_DIR = AIR_DIR / "Sever"
STATE_FILE = UPLOAD_DIR / "last.json"   # тут сохраним путь к последнему обработанному

# Хранилище файлов

LAST_SAVED_PATH = None
