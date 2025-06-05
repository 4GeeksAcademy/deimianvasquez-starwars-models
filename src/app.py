"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200


@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    firstname = data.get('firstname')
    email = data.get('email')

    if not username or not firstname or not email:
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    # Verifica si el email ya existe
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "El email ya está registrado"}), 400

    new_user = User(username=username, firstname=firstname, email=email)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "Usuario registrado exitosamente", "user": new_user.serialize()}), 201


@app.route('/follow', methods=['POST'])
def follow_user():
    data = request.get_json()
    user_from_id = data.get('user_from_id')
    user_to_id = data.get('user_to_id')

    if not user_from_id or not user_to_id:
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    if user_from_id == user_to_id:
        return jsonify({"error": "Un usuario no puede seguirse a sí mismo"}), 400

    user_from = User.query.get(user_from_id)
    user_to = User.query.get(user_to_id)

    if not user_from or not user_to:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if user_to in user_from.following_assoc:
        return jsonify({"error": "Ya sigues a este usuario"}), 400

    user_from.following_assoc.append(user_to)
    db.session.commit()

    return jsonify({
        "msg": f"{user_from.username} ahora sigue a {user_to.username}",
        "following": [u.serialize() for u in user_from.following_assoc]
    }), 200


@app.route('/user/<int:user_id>/following', methods=['GET'])
def get_following(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    following = [u.serialize() for u in user.following_assoc]
    return jsonify({"user_id": user_id, "following": following}), 200


@app.route('/user/<int:user_id>/followers', methods=['GET'])
def get_followers(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    followers = [u.serialize() for u in user.followers_assoc]
    return jsonify({"user_id": user_id, "followers": followers}), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
