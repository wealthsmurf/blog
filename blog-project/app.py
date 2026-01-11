import os
import sqlite3
import markdown
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# [배포용 설정] Render Disk 연결 시 /data 폴더를 사용, 아니면 현재 폴더 사용
BASE_DIR = '/data' if os.path.exists('/data') else os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'blog.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')

# 폴더 생성 로직
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            title TEXT, 
            category TEXT, 
            content TEXT, 
            image_file TEXT
        )
    ''')
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute('SELECT title, category, content, image_file FROM posts ORDER BY id DESC')
    posts = []
    for row in cur.fetchall():
        rendered_content = markdown.markdown(row[2], extensions=['fenced_code', 'codehilite'])
        posts.append({'title': row[0], 'category': row[1], 'content': rendered_content, 'image': row[3]})
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/save', methods=['POST'])
def save():
    title = request.form.get('title')
    category = request.form.get('category')
    content = request.form.get('content')
    code_content = request.form.get('code_content')
    file = request.files.get('image')
    
    if category == '개발' and code_content:
        content = f"{content}\n\n**[Source Code]**\n```\n{code_content}\n```"

    filename = ""
    if file and file.filename != '':
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT INTO posts (title, category, content, image_file) VALUES (?, ?, ?, ?)', 
                 (title, category, content, filename))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0') # 배포용 설정
