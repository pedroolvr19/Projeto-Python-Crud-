import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone
        }

@app.route('/')
def index_with_form():
    return render_template('index.html')

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    
    if not data or not 'email' in data or not 'nome' in data or not 'password' in data:
        return jsonify({"error": "Dados incompletos: nome, email e password são obrigatórios"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email já cadastrado"}), 400

    new_user = User(
        nome=data['nome'],
        email=data['email'],
        telefone=data.get('telefone')
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify(new_user.to_dict()), 201

@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    users_list = [user.to_dict() for user in users]
    return jsonify(users_list)

@app.route('/user/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_dict())

@app.route('/user/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json()
    
    user.nome = data.get('nome', user.nome)
    user.email = data.get('email', user.email)
    user.telefone = data.get('telefone', user.telefone)
    
    if 'password' in data and data['password']:
        user.set_password(data['password'])
        
    db.session.commit()
    return jsonify(user.to_dict())

@app.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"Usuário {user.nome} (ID: {id}) deletado com sucesso."})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)