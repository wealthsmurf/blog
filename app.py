import os
import psycopg2  # sqlite3 대신 사용
import markdown
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Supabase에서 복사한 URI 주소를 여기에 넣으세요
# Render에 배포할 때는 환경변수로 설정하는 것이 안전합니다.
DB_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DB_URL)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY, 
            title TEXT NOT NULL, 
            category TEXT, 
            content TEXT, 
            image_file TEXT
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT title, category, content, image_file FROM posts ORDER BY id DESC')
    posts = []
    for row in cur.fetchall():
        rendered_content = markdown.markdown(row[2], extensions=['fenced_code', 'codehilite'])
        posts.append({'title': row[0], 'category': row[1], 'content': rendered_content, 'image': row[3]})
    cur.close()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/save', methods=['POST'])
def save():
    title = request.form.get('title')
    category = request.form.get('category')
    content = request.form.get('content')
    code_content = request.form.get('code_content')
    
    if category == '개발' and code_content:
        content = f"{content}\n\n**[Source Code]**\n```\n{code_content}\n```"

    # 이미지 저장은 Render 무료 플랜 특성상 초기화되므로 
    # 텍스트 데이터 보존에 집중한 예시입니다.
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO posts (title, category, content, image_file) VALUES (%s, %s, %s, %s)', 
                 (title, category, content, ""))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
