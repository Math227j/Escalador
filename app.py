import calendar
import datetime
import random
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user, login_required,
                         logout_user, current_user)

# Inicializando o app Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'minha_chave_super_secreta'  # Substitua por uma chave segura
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configuração do Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modelo de usuário para login
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)  # Armazena senha simples

# Carregamento do usuário
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rota principal: redireciona para a escala (usuário logado)
@app.route('/')
@login_required
def home():
    return redirect(url_for('escala'))

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Validação sem hash de senha
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user, remember=True)  # Sessão persistente
            return redirect(url_for('escala'))
        else:
            flash("Credenciais inválidas. Tente novamente.", "danger")
    return render_template('login.html')

# Rota de cadastro de usuário
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash("Usuário já existe. Tente outro nome.", "danger")
        else:
            new_user = User(username=username, password=password)  # Armazena senha simples
            db.session.add(new_user)
            db.session.commit()
            flash("Cadastro realizado com sucesso. Faça login!", "success")
            return redirect(url_for('login'))
    return render_template('cadastro.html')

# Rota para logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Rota para gerenciar participantes (registro de nomes)
@app.route('/participants', methods=['GET', 'POST'])
@login_required
def participants():
    if request.method == 'POST':
        name = request.form['name']
        gender = request.form['gender']
        if name:
            new_participant = Participant(name=name, gender=gender)
            db.session.add(new_participant)
            db.session.commit()
            flash(f"{name} adicionado(a) com sucesso!", "success")
        else:
            flash("Nome inválido!", "danger")
        return redirect(url_for('participants'))
    all_participants = Participant.query.all()
    return render_template('participants.html', participants=all_participants)

# Rota para remover participante
@app.route('/remove_participant/<int:id>')
@login_required
def remove_participant(id):
    p = Participant.query.get(id)
    if p:
        db.session.delete(p)
        db.session.commit()
        flash(f"{p.name} removido(a) com sucesso!", "success")
    else:
        flash("Participante não encontrado!", "danger")
    return redirect(url_for('participants'))

# Função para gerar a escala para quartas, sábados e domingos do mês atual
def generate_schedule(year, month):
    men = Participant.query.filter_by(gender="homem").all()
    women = Participant.query.filter_by(gender="mulher").all()
    if len(men) < 2 or len(women) < 2:
        flash("Cadastre pelo menos 2 homens e 2 mulheres para gerar a escala.", "danger")
        return {}
    schedule = {}
    num_days = calendar.monthrange(year, month)[1]
    for day in range(1, num_days + 1):
        date_obj = datetime.date(year, month, day)
        if date_obj.weekday() in [2, 5, 6]:  # 2 = quarta, 5 = sábado, 6 = domingo
            try:
                selected_men = random.sample(men, 2)
                selected_women = random.sample(women, 2)
                schedule[date_obj.strftime("%Y-%m-%d")] = {
                    "homens": [m.name for m in selected_men],
                    "mulheres": [w.name for w in selected_women]
                }
            except ValueError:
                flash("Erro ao sortear participantes para o dia " + date_obj.strftime("%Y-%m-%d"), "danger")
    return schedule

# Rota para exibir a escala gerada automaticamente
@app.route('/escala')
@login_required
def escala():
    today = datetime.date.today()
    year = today.year
    month = today.month
    schedule = generate_schedule(year, month)
    formatted_schedule = ""
    for date_str, s in schedule.items():
        formatted_schedule += f"Data: {date_str}\n"
        formatted_schedule += f"  Homens: {', '.join(s['homens'])}\n"
        formatted_schedule += f"  Mulheres: {', '.join(s['mulheres'])}\n\n"
    return render_template('escala.html', schedule=schedule, formatted_schedule=formatted_schedule, year=year, month=month)

# Criação das tabelas (se não existirem)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
