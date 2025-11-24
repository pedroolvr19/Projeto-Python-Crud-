import os
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-segura'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')

    query = User.query

    if search_query:
        query = query.filter(
            (User.nome.contains(search_query)) | 
            (User.email.contains(search_query))
        )

    users_pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=5)

    return render_template('index.html', users=users_pagination, search_query=search_query)

@app.route('/user/add', methods=['POST'])
def add_user():
    nome = request.form.get('nome')
    email = request.form.get('email')
    password = request.form.get('password')
    telefone = request.form.get('telefone')

    if not nome or not email or not password:
        flash('Nome, Email e Senha são obrigatórios!', 'danger')
        return redirect(url_for('index'))

    if User.query.filter_by(email=email).first():
        flash('Este email já está cadastrado.', 'warning')
        return redirect(url_for('index'))

    new_user = User(nome=nome, email=email, telefone=telefone)
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        flash(f'Usuário {nome} criado com sucesso!', 'success')
    except:
        db.session.rollback()
        flash('Erro ao criar usuário no banco de dados.', 'danger')

    return redirect(url_for('index'))

@app.route('/user/update/<int:id>', methods=['POST'])
def update_user(id):
    user = User.query.get_or_404(id)
    
    user.nome = request.form.get('nome')
    user.email = request.form.get('email')
    user.telefone = request.form.get('telefone')
    
    new_password = request.form.get('password')
    if new_password:
        user.set_password(new_password)
        
    try:
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'info')
    except:
        flash('Erro ao atualizar. Verifique se o email já existe.', 'danger')

    return redirect(url_for('index'))

@app.route('/user/delete/<int:id>')
def delete_user(id):
    user = User.query.get_or_404(id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Usuário removido com sucesso.', 'dark')
    except:
        flash('Erro ao deletar usuário.', 'danger')
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
