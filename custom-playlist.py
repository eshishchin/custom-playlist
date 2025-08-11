from flask import Flask, request, render_template_string, redirect, url_for
import datetime
import os
from collections import defaultdict
import shutil

app = Flask(__name__)

# Конфигурация по умолчанию
FOOD_KEYWORDS = []
LINERS = [
    "CCA-sare.wav",
    "CCA-mesele.wav",
    "CCA-5fructe.wav",
    "CCA-30min.wav",
    "CCA-2litri.wav"
]

# Базовый индекс (сдвиг по дням)
BASE_INDEX = datetime.date.today().toordinal()
LAST_SAVED_PATH = None

UPLOAD_TEMPLATE = """
<h2>Загрузка рекламного плейлиста</h2>
<form method="post" enctype="multipart/form-data">
    <label>Ключевые слова (отметьте нужные):</label><br>
    <input type="checkbox" name="food_keywords" value="Kauf"> Kauf<br>
    <input type="checkbox" name="food_keywords" value="Local"> Local<br>
    <input type="checkbox" name="food_keywords" value="Kfc"> Kfc<br>
    <input type="checkbox" name="food_keywords" value="Linella"> Linella<br><br>
    <label>Файл плейлиста:</label><br>
    <input type="file" name="playlist"><br><br>
    <input type="submit" value="Обработать">
</form>
<p><a href="/generate-north">Собрать плейлист для Бельц</a></p>
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
<a href="/">Назад</a> | <a href="/upload-to-air">Загрузить на эфир</a>
"""

@app.route('/upload-to-air')
def upload_to_air():
    global LAST_SAVED_PATH
    if LAST_SAVED_PATH and os.path.exists(LAST_SAVED_PATH):
        dest = os.path.join("/mnt/synadyn/!Playlist/Reclama/", os.path.basename(LAST_SAVED_PATH))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy(LAST_SAVED_PATH, dest)
        return f"<p>Файл загружен на эфир: {dest}</p><a href='/'>Назад</a>"
    return "<p>Файл не найден. Сначала загрузите и обработайте плейлист.</p><a href='/'>Назад</a>"

@app.route('/', methods=['GET', 'POST'])
def index():
    global FOOD_KEYWORDS, LINERS, LAST_SAVED_PATH
    if request.method == 'POST':
        FOOD_KEYWORDS = request.form.getlist('food_keywords')
        file = request.files['playlist']
        fn = os.path.basename(file.filename)
        path = os.path.join('uploaded', fn)
        os.makedirs('uploaded', exist_ok=True)
        file.save(path)
        shutil.copy(path, path + '.bak')
        try:
            lines = open(path, encoding='utf-8').read().splitlines()
        except UnicodeDecodeError:
            lines = open(path, encoding='cp1251').read().splitlines()
        blocks = defaultdict(list)
        for ln in lines:
            parts = ln.split('\t')
            if len(parts)!=2: continue
            t, pth = parts
            blocks[t].append(pth.strip('"'))
        proc = {}
        for idx, (t, arr) in enumerate(blocks.items()):
            if any(word.lower() in x.lower() for x in arr for word in FOOD_KEYWORDS) and LINERS:
                for i in reversed(range(len(arr))):
                    if 'zakr_00_737-446.mp3' in arr[i]:
                        arr.insert(i, f"Реклама*Roliki\\{LINERS[(BASE_INDEX+idx)%len(LINERS)]}")
                        break
            proc[t] = arr
        with open(path, 'wb') as f:
            for t, arr in proc.items():
                for x in arr:
                    f.write(f"{t}\t\"{x}\"\r\n".encode('cp1251',errors='replace'))
        LAST_SAVED_PATH = path
        return render_template_string(RESULT_TEMPLATE, blocks=proc)
    return render_template_string(UPLOAD_TEMPLATE)

@app.route('/generate-north', methods=['GET','POST'])
def generate_north():
    global LAST_SAVED_PATH
    if not LAST_SAVED_PATH or not os.path.exists(LAST_SAVED_PATH):
        return "<p>Сначала загрузите и обработайте основной плейлист.</p><a href='/'>Назад</a>"
    if request.method=='POST':
        data = request.form.get('rows','')
        rows = data.splitlines() if data else []
        ins_map, del_map, line_map = {}, {}, set()
        for r in rows:
            parts = r.split('|')
            if len(parts)!=4: continue
            dt, ins, dels, lin = parts
            try:
                date, time = dt.strip().split(' ')
            except ValueError:
                continue
            key = time
            ins_map[key] = [x.strip() for x in ins.split(',') if x.strip()]
            del_map[key] = [x.strip().lower() for x in dels.split(',') if x.strip()]
            if lin=='yes': line_map.add(key)
        lines = []
        try:
            lines = open(LAST_SAVED_PATH, encoding='cp1251').read().splitlines()
        except:
            return "<p>Ошибка при чтении файла.</p><a href='/'>Назад</a>"
        blocks = defaultdict(list)
        for ln in lines:
            parts=ln.split('\t')
            if len(parts)!=2: continue
            t,p=parts; blocks[t].append(p.strip('"'))
        sever = {}
        for k, iv in ins_map.items():
            if k not in blocks: continue
            bl = [x for x in blocks[k] if not any(dw in x.lower() for dw in del_map.get(k,[]))]
            if k in line_map and iv:
                for i in reversed(range(len(bl))):
                    if 'zakr_00_737-446.mp3' in bl[i]: bl.insert(i, f"Реклама*Roliki_B\\{iv[0]}"); break
            ins_list = [f"Реклама*Roliki_B\\{x}" for x in iv]
            pos = next((i+1 for i,v in enumerate(bl) if 'реклама' in v.lower()),1)
            bl[pos:pos]=ins_list
            if bl: bl=bl[:-1]
            sever[k]=bl
        out = os.path.join('/mnt/synadyn/!Playlist/Reclama/Sever', os.path.basename(LAST_SAVED_PATH))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out,'wb') as f:
            for t,arr in sever.items():
                for x in arr: f.write(f"{t}\t\"{x}\"\r\n".encode('cp1251',errors='replace'))
        return f"<p>Северный плейлист сохранён: {out}</p><a href='/'>Назад</a>"
    return render_template_string("""
    <h2>Создание плейлиста для Бельц</h2>
    <form method="post" onsubmit="prepareData(event)">
        <table id="block-table" border="1" cellpadding="5">
            <tr><th>Дата и время (DD.MM.YYYY HH:MM:SS)</th><th>Insert</th><th>Delete</th><th>Liner</th></tr>
        </table>
        <button type="button" onclick="addRow()">Добавить строку</button><br><br>
        <input type="hidden" name="rows" id="rows">
        <input type="submit" value="Собрать">
    </form>
    <a href='/'>Назад</a>
    <script>
    function addRow(){const t=document.getElementById('block-table');const r=t.insertRow();r.insertCell(0).innerHTML="<input type='text' placeholder='23.07.2025 06:50:00'>";r.insertCell(1).innerHTML="<input type='text' placeholder='insert1.wav, insert2.wav'>";r.insertCell(2).innerHTML="<input type='text' placeholder='ключевые слова'>";r.insertCell(3).innerHTML="<select><option value='no'>Нет</option><option value='yes'>Да</option></select>";}
    function prepareData(e){e.preventDefault();const t=document.getElementById('block-table');const a=[];for(let i=1;i<t.rows.length;i++){const c=t.rows[i].cells;const d=c[0].querySelector('input').value;const ins=c[1].querySelector('input').value;const dl=c[2].querySelector('input').value;const ln=c[3].querySelector('select').value;a.push(`${d}|${ins}|${dl}|${ln}`);}document.getElementById('rows').value = a.join('
');e.target.submit();}
    </script>
    """)

if __name__=='__main__':
    app.run(debug=True,host='0.0.0.0',port=8081)
