from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from docx import Document
import random
from whitenoise import WhiteNoise

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PREFERRED_URL_SCHEME'] = 'https'

# WhiteNoise'u ekle
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    native_language = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

# Oturum kontrolü için decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    user = User.query.get(session['user_id'])
    return render_template('home.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        else:
            flash('Geçersiz email veya şifre!')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        password = request.form['password']
        city = request.form['city']
        native_language = request.form['native_language']
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Bu email adresi zaten kayıtlı!')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, surname=surname, email=email, password=hashed_password, city=city, native_language=native_language)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

def read_qa_from_docx(level):
    qa_pairs = []
    
    # A1 seviyesi için sabit soru-cevapları
    if level == 'A1':
        qa_pairs = [
            {"question": "Von welchem Gleis ist die Abfahrt vom Zug?", "answer": "Die Abfahrt ist vom Gleis 5."},
            {"question": "Wie lange dauert der Flug nach Berlin?", "answer": "Der Flug dauert zwei Stunden."},
            {"question": "Wohin fährt der Bus?", "answer": "Er fährt zum Hauptbahnhof."},
            {"question": "Wann ist die Ankunft vom ICE?", "answer": "Die Ankunft ist um 16:45 Uhr."},
            {"question": "Auf welchem Gleis kommt der Zug an?", "answer": "Er kommt auf dem nächsten Gleis an."},
            {"question": "Kann ich zu Fuß zum Bahnhof gehen?", "answer": "Ja, das dauert nur 10 Minuten."},
            {"question": "Wo ist der nächste Flughafen?", "answer": "Der Flughafen ist in der Nähe der Autobahn."},
            {"question": "Wann fährt der Zug ab?", "answer": "Der Zug fährt um 10:30 Uhr ab."},
            {"question": "Wie lange dauert es zu Fuß ins Stadtzentrum?", "answer": "Es dauert etwa 20 Minuten."},
            {"question": "Wohin fliegt das nächste Flugzeug?", "answer": "Das nächste Flugzeug fliegt nach München."}
        ]
        return qa_pairs
    
    # Diğer seviyeler için docx dosyalarından okuma
    folder_path = 'Frage-Antwort'
    if level == 'A2':
        files = ['A2.docx', 'A2(2).docx', 'A2_B1.docx']
    elif level == 'B1':
        files = ['B1.docx', 'B1(1).docx', 'A2_B1.docx']
    else:
        return qa_pairs
    
    # Her dosyadan soru-cevapları oku
    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        if os.path.exists(file_path):
            doc = Document(file_path)
            current_question = None
            current_answer = []
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                    
                # Soru ve cevap formatını kontrol et
                if text.startswith('F:'):
                    # Önceki soru-cevap çiftini kaydet
                    if current_question and current_answer:
                        qa_pairs.append({
                            "question": current_question,
                            "answer": " ".join(current_answer)
                        })
                    current_question = text[2:].strip()
                    current_answer = []
                elif text.startswith('A:'):
                    current_answer.append(text[2:].strip())
            
            # Son soru-cevap çiftini kaydet
            if current_question and current_answer:
                qa_pairs.append({
                    "question": current_question,
                    "answer": " ".join(current_answer)
                })
    
    return qa_pairs

@app.route('/frage-antwort')
def frage_antwort():
    # A1 seviyesi için sabit soru-cevapları
    a1_exercises = [
        {'title': 'Frage-Antwort 1', 'file': 'frage_antwort1.html'},
        {'title': 'Frage-Antwort 2', 'file': 'frage_antwort2.html'},
        {'title': 'Frage-Antwort 3', 'file': 'frage_antwort3.html'}
    ]
    
    # B1 seviyesi için sabit soru-cevapları
    b1_exercises = [
        {'title': 'Frage-Antwort 6', 'file': 'frage_antwort6.html'},
        {'title': 'Frage-Antwort 7', 'file': 'frage_antwort7.html'}
    ]
    
    # B2 seviyesi için sabit soru-cevapları
    b2_exercises = [
        {'title': 'Frage-Antwort 8', 'file': 'frage_antwort8.html'},
        {'title': 'Frage-Antwort 9', 'file': 'frage_antwort9.html'}
    ]
    
    return render_template('frage_antwort_list.html',
                         a1_exercises=a1_exercises,
                         b1_exercises=b1_exercises,
                         b2_exercises=b2_exercises)

@app.route('/frage-antwort/<exercise>')
def frage_antwort_exercise(exercise):
    return render_template(exercise)

@app.route('/diktat')
@login_required
def diktat():
    return render_template('diktat.html')

@app.route('/grammar')
@login_required
def grammar():
    a1_exercises = [
        {'title': 'Grammatik Übung 1', 'file': 'grammar.html'},
        {'title': 'Grammatik Übung 2', 'file': 'grammar2.html'},
        {'title': 'Grammatik Übung 3', 'file': 'grammar3.html'},
        {'title': 'Grammatik Übung 4', 'file': 'grammar4.html'}
    ]
    
    a2_exercises = [
        {'title': 'Grammatik Übung 5', 'file': 'grammar5.html'},
        {'title': 'Grammatik Übung 6', 'file': 'grammar6.html'},
        {'title': 'Grammatik Übung 7', 'file': 'grammar7.html'},
        {'title': 'Grammatik Übung 8', 'file': 'grammar8.html'}
    ]
    
    b1_exercises = [
        {'title': 'Grammatik Übung 9', 'file': 'grammar9.html'},
        {'title': 'Grammatik Übung 10', 'file': 'grammar10.html'},
        {'title': 'Grammatik Übung 11', 'file': 'grammar11.html'},
        {'title': 'Grammatik Übung 12', 'file': 'grammar12.html'}
    ]
    
    b2_exercises = [
        {'title': 'Grammatik Übung 13', 'file': 'grammar13.html'},
        {'title': 'Grammatik Übung 14', 'file': 'grammar14.html'},
        {'title': 'Grammatik Übung 15', 'file': 'grammar15.html'},
        {'title': 'Grammatik Übung 16', 'file': 'grammar16.html'},
        {'title': 'Grammatik Übung 17', 'file': 'grammar17.html'}
    ]
    
    return render_template('grammar_list.html',
                         a1_exercises=a1_exercises,
                         a2_exercises=a2_exercises,
                         b1_exercises=b1_exercises,
                         b2_exercises=b2_exercises)

@app.route('/grammar/<exercise>')
@login_required
def grammar_exercise(exercise):
    return render_template(exercise)

@app.route('/musik')
@login_required
def musik():
    return render_template('musik.html')

@app.route('/leseverstehen')
@login_required
def leseverstehen():
    a1_exercises = [
        {'title': 'Leseverstehen 1', 'file': 'leseverstehen1.html'},
        {'title': 'Leseverstehen 2', 'file': 'leseverstehen2.html'},
        {'title': 'Leseverstehen 3', 'file': 'leseverstehen3.html'}
    ]
    
    a2_exercises = [
        {'title': 'Leseverstehen 4', 'file': 'leseverstehen4.html'},
        {'title': 'Leseverstehen 5', 'file': 'leseverstehen5.html'},
        {'title': 'Leseverstehen 6', 'file': 'leseverstehen6.html'}
    ]
    
    b1_exercises = [
        {'title': 'Leseverstehen 7', 'file': 'leseverstehen7.html'},
        {'title': 'Leseverstehen 8', 'file': 'leseverstehen8.html'},
        {'title': 'Leseverstehen 9', 'file': 'leseverstehen9.html'},
        {'title': 'Leseverstehen 10', 'file': 'leseverstehen10.html'},
        {'title': 'Leseverstehen 11', 'file': 'leseverstehen11.html'},
        {'title': 'Leseverstehen 12', 'file': 'leseverstehen12.html'},
        {'title': 'Leseverstehen 13', 'file': 'leseverstehen13.html'},
        {'title': 'Leseverstehen 14', 'file': 'leseverstehen14.html'}
    ]
    
    b2_exercises = [
        {'title': 'Leseverstehen 15', 'file': 'leseverstehen15.html'}
    ]
    
    return render_template('leseverstehen_list.html',
                         a1_exercises=a1_exercises,
                         a2_exercises=a2_exercises,
                         b1_exercises=b1_exercises,
                         b2_exercises=b2_exercises)

@app.route('/leseverstehen/<exercise>')
@login_required
def leseverstehen_exercise(exercise):
    return render_template(exercise)

@app.route('/multiple_choice')
@login_required
def multiple_choice():
    user = User.query.get(session['user_id'])
    # Sadece multiple choice alıştırmaları
    multiple_choice_templates = [
        'multiple_choice1.html',
        'multiple_choice2.html',
        'multiple_choice3.html',
        'multiple_choice4.html',
        'multiple_choice5.html',
        'multiple_choice6.html',
        'multiple_choice7.html',
        'multiple_choice8.html'
    ]
    template = random.choice(multiple_choice_templates)
    return render_template(template, user=user)

@app.route('/satze_bilden')
@login_required
def satze_bilden():
    user = User.query.get(session['user_id'])
    # Sätze bilden alıştırmaları için 14-27 arası
    exercise = random.choice(['grammar14.html', 'grammar15.html', 'grammar16.html', 'grammar17.html', 'grammar18.html', 'grammar19.html', 'grammar20.html', 'grammar21.html', 'grammar22.html', 'grammar23.html', 'grammar24.html', 'grammar25.html', 'grammar26.html', 'grammar27.html'])
    return render_template(exercise, user=user)

@app.route('/kommunikation')
@login_required
def kommunikation():
    return render_template('kommunikation.html')

@app.route('/wortschatz')
@login_required
def wortschatz():
    a1_exercises = [
        {'title': 'Wortschatz 1', 'file': 'wortschatz1.html'},
        {'title': 'Wortschatz 2', 'file': 'wortschatz2.html'},
        {'title': 'Wortschatz 3', 'file': 'wortschatz3.html'},
        {'title': 'Wortschatz 4', 'file': 'wortschatz4.html'}
    ]
    
    a2_exercises = [
        {'title': 'Wortschatz 5', 'file': 'wortschatz5.html'},
        {'title': 'Wortschatz 6', 'file': 'wortschatz6.html'},
        {'title': 'Wortschatz 7', 'file': 'wortschatz7.html'},
        {'title': 'Wortschatz 8', 'file': 'wortschatz8.html'}
    ]
    
    b1_exercises = [
        {'title': 'Wortschatz 9', 'file': 'wortschatz9.html'},
        {'title': 'Wortschatz 10', 'file': 'wortschatz10.html'},
        {'title': 'Wortschatz 11', 'file': 'wortschatz11.html'},
        {'title': 'Wortschatz 12', 'file': 'wortschatz12.html'}
    ]
    
    b2_exercises = [
        {'title': 'Wortschatz 13', 'file': 'wortschatz13.html'},
        {'title': 'Wortschatz 14', 'file': 'wortschatz14.html'},
        {'title': 'Wortschatz 15', 'file': 'wortschatz15.html'}
    ]
    
    return render_template('wortschatz_list.html',
                         a1_exercises=a1_exercises,
                         a2_exercises=a2_exercises,
                         b1_exercises=b1_exercises,
                         b2_exercises=b2_exercises)

@app.route('/wortschatz/<exercise>')
@login_required
def wortschatz_exercise(exercise):
    return render_template(exercise)

@app.route('/zuordnung')
@login_required
def zuordnung():
    user = User.query.get(session['user_id'])
    # Sadece zuordnung alıştırmaları
    zuordnung_templates = [
        'grammar28.html',
        'grammar29.html',
        'grammar30.html',
        'grammar31.html',
        'grammar32.html',
        'grammar33.html',
        'grammar34.html',
        'grammar35.html',
        'grammar36.html'
    ]
    template = random.choice(zuordnung_templates)
    return render_template(template, user=user)

@app.route('/grammar18')
@login_required
def grammar18():
    return render_template('grammar18.html')

@app.route('/grammar19')
@login_required
def grammar19():
    return render_template('grammar19.html')

@app.route('/grammar20')
@login_required
def grammar20():
    return render_template('grammar20.html')

@app.route('/grammar21')
@login_required
def grammar21():
    return render_template('grammar21.html')

@app.route('/grammar22')
@login_required
def grammar22():
    return render_template('grammar22.html')

@app.route('/grammar23')
@login_required
def grammar23():
    return render_template('grammar23.html')

@app.route('/grammar24')
@login_required
def grammar24():
    return render_template('grammar24.html')

@app.route('/grammar25')
@login_required
def grammar25():
    return render_template('grammar25.html')

@app.route('/grammar26')
@login_required
def grammar26():
    return render_template('grammar26.html')

@app.route('/grammar27')
@login_required
def grammar27():
    return render_template('grammar27.html')

@app.route('/grammar28')
@login_required
def grammar28():
    return render_template('grammar28.html')

@app.route('/grammar29')
@login_required
def grammar29():
    return render_template('grammar29.html')

@app.route('/grammar30')
@login_required
def grammar30():
    return render_template('grammar30.html')

@app.route('/grammar31')
@login_required
def grammar31():
    return render_template('grammar31.html')

@app.route('/grammar32')
@login_required
def grammar32():
    return render_template('grammar32.html')

@app.route('/grammar35')
@login_required
def grammar35():
    return render_template('grammar35.html')

@app.route('/grammar36')
@login_required
def grammar36():
    return render_template('grammar36.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port) 