import os
import psycopg2
import markdown
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Railway의 PostgreSQL 연결 정보는 'DATABASE_URL' 환경 변수에 저장됩니다.
# 로컬 테스트 시에는 직접 주소를 입력하거나 .env 파일을 사용할 수 있습니다.
DATABASE_URL = os.environ.get('trolley.proxy.rlwy.net:38739')

def get_db_connection():
    # sslmode='require'는 Railway/Supabase 등 클라우드 DB 연결 시 필수 보안 설정입니다.
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # SERIAL을 사용하여 ID 자동 생성, 데이터는 DB 서비스에 영구 저장됩니다.
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
        # 마크다운 렌더링 (코드 하이라이팅 확장 포함)
        rendered_content = markdown.markdown(row[2], extensions=['fenced_code', 'codehilite'])
        posts.append({
            'title': row[0], 
            'category': row[1], 
            'content': rendered_content, 
            'image': row[3]
        })
    cur.close()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/save', methods=['POST'])
def save():
    title = request.form.get('title')
    category = request.form.get('category')
    content = request.form.get('content')
    code_content = request.form.get('code_content')
    
    # 개발 카테고리일 경우 소스코드 블록 추가
    if category == '개발' and code_content:
        content = f"{content}\n\n**[Source Code]**\n```\n{code_content}\n```"

    conn = get_db_connection()
    cur = conn.cursor()
    # SQL 인젝션 방지를 위해 %s 플레이스홀더 사용
    cur.execute('INSERT INTO posts (title, category, content, image_file) VALUES (%s, %s, %s, %s)', 
                 (title, category, content, ""))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # 테이블이 없으면 생성
    init_db()
    
    # Railway 배포 환경을 위한 포트 및 호스트 설정
    port = int(os.environ.get("PORT", 5000))

    app.run(host='0.0.0.0', port=port)
