import os
import shutil
from flask import Flask, render_template

app = Flask(__name__)

# Tüm route'ları tanımla
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/frage-antwort')
def frage_antwort():
    return render_template('frage_antwort_list.html')

@app.route('/grammar')
def grammar():
    return render_template('grammar_list.html')

@app.route('/leseverstehen')
def leseverstehen():
    return render_template('leseverstehen_list.html')

@app.route('/wortschatz')
def wortschatz():
    return render_template('wortschatz_list.html')

# Diğer route'ları da ekle...

# Statik dosyaları kopyala
def copy_static_files():
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    os.makedirs('dist')
    
    # templates klasöründeki tüm HTML dosyalarını kopyala
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                src_path = os.path.join(root, file)
                dst_path = os.path.join('dist', file)
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
    
    # static klasörünü kopyala
    if os.path.exists('static'):
        shutil.copytree('static', 'dist/static')

if __name__ == '__main__':
    copy_static_files()
    print("Statik site oluşturuldu!") 