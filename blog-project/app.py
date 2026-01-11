import os
import sqlite3
import markdown
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect('blog.db')
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
    conn = sqlite3.connect('blog.db')
    cur = conn.execute('SELECT title, category, content, image_file FROM posts ORDER BY id DESC')
    posts = []
    for row in cur.fetchall():
        # 마크다운 변환 시 코드 하이라이팅 확장 기능 사용
        rendered_content = markdown.markdown(row[2], extensions=['fenced_code', 'codehilite'])
        posts.append({'title': row[0], 'category': row[1], 'content': rendered_content, 'image': row[3]})
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/save', methods=['POST'])
def save():
    title = request.form.get('title')
    category = request.form.get('category')
    content = request.form.get('content')
    code_content = request.form.get('code_content') # 코드 칸 데이터
    file = request.files.get('image')
    
    # 개발 로그라면 코드 칸의 내용을 본문 뒤에 마크다운 형식으로 붙임
    if category == '개발' and code_content:
        content = f"{content}\n\n**[Source Code]**\n```\n{code_content}\n```"

    filename = ""
    if file and file.filename != '':
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = sqlite3.connect('blog.db')
    conn.execute('INSERT INTO posts (title, category, content, image_file) VALUES (?, ?, ?, ?)', 
                 (title, category, content, filename))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)