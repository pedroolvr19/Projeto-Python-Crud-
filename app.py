import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# --- Configuração ---

# Cria a instância do aplicativo Flask
app = Flask(__name__)

# Define o caminho base do diretório
basedir = os.path.abspath(os.path.dirname(__file__))

# Configuração do Banco de Dados SQLite
# Ele criará um arquivo 'database.db' no mesmo diretório
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o SQLAlchemy
db = SQLAlchemy(app)

# --- Modelo (Model) ---

# Define o modelo de dados 'User' para o banco de dados
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    # Armazenamos o HASH da senha, e não a senha pura
    password_hash = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)

    # Método para definir a senha (cria o hash)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Método para verificar a senha (compara o hash)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Método para serializar o objeto (transformar em JSON)
    # Não incluímos a senha no retorno por segurança
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone
        }

# --- Rotas da API (Endpoints CRUDS) ---

# Rota de health check (apenas para ver se a API está no ar)
@app.route('/')
def index():
    return jsonify({"message": "API de Usuários está no ar!"})

# CREATE: Criar um novo usuário (POST)
@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # Validação simples de entrada
    if not data or not 'email' in data or not 'password' in data or not 'nome' in data:
        return jsonify({"error": "Dados incompletos: nome, email e password são obrigatórios"}), 400

    # Verifica se o email já existe
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email já cadastrado"}), 400

    # Cria o novo usuário
    new_user = User(
        nome=data['nome'],
        email=data['email'],
        telefone=data.get('telefone') # .get() é seguro se a chave não existir
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify(new_user.to_dict()), 201 # 201 = Created

# READ (All): Obter todos os usuários (GET)
@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    # Converte a lista de usuários para uma lista de dicionários
    users_list = [user.to_dict() for user in users]
    return jsonify(users_list)

# READ (One): Obter um usuário por ID (GET)
@app.route('/user/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id) # Retorna 404 se não encontrar
    return jsonify(user.to_dict())

# UPDATE: Atualizar um usuário (PUT)
@app.route('/user/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json()
    
    # Atualiza os campos (se eles existirem no JSON)
    user.nome = data.get('nome', user.nome)
    user.email = data.get('email', user.email)
    user.telefone = data.get('telefone', user.telefone)
    
    # Atualiza a senha apenas se uma nova foi fornecida
    if 'password' in data and data['password']:
        user.set_password(data['password'])
        
    db.session.commit()
    return jsonify(user.to_dict())

# DELETE: Deletar um usuário (DELETE)
@app.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"Usuário {user.nome} (ID: {id}) deletado com sucesso."})


# --- Execução ---

if __name__ == '__main__':
    # Bloco para criar o banco de dados e as tabelas (apenas na primeira execução)
    with app.app_context():
        db.create_all()
    
    # Roda o aplicativo
    # debug=True reinicia o servidor automaticamente a cada mudança
    app.run(debug=True)