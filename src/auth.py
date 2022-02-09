from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
import validators
from constants.http_status_codes import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT, HTTP_201_CREATED, \
    HTTP_401_UNAUTHORIZED, HTTP_200_OK
from src.database import User, db

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth.post("/register")
def register():
    username = request.json["username"]
    password = request.json["password"]
    email = request.json["email"]

    if len(username) < 3:
        return jsonify({
            "error": "username too short"
        }), HTTP_400_BAD_REQUEST

    if len(password) < 6:
        return jsonify({
            "error": "password too short"
        }), HTTP_400_BAD_REQUEST

    if not username.isalnum() or " " in username:
        return jsonify(
            {
                "error": "username must be alphanumeric with no spaces"
            }
        ), HTTP_400_BAD_REQUEST

    if not validators.email(email):
        return jsonify(
            {
                "error": "email invalid"
            }
        ), HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first() is not None:
        return jsonify(
            {
                "error": "email taken"
            }
        ), HTTP_409_CONFLICT

    if User.query.filter_by(username=username).first() is not None:
        return jsonify(
            {
                "error": "username taken"
            }
        ), HTTP_409_CONFLICT

    password_hash = generate_password_hash(password)
    user = User(username=username, password=password_hash, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify(
        {
            "message": "User successfully created",
            "user": {
                "username": username,
                "email": email
            }
        }
    ), HTTP_201_CREATED


@auth.post("/login")
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    user = User.query.filter_by(email=email).first()
    print(user.username)

    if user:
        is_pass_correct = check_password_hash(user.password, password)

        if is_pass_correct:
            refresh_token = create_refresh_token(identity=user.id)
            access_token = create_access_token(identity=user.id)

            return jsonify(
                {
                    "user": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "username": user.username,
                        "email": user.email
                    }
                }
            ), HTTP_200_OK

    return jsonify(
        {
            "error": "Wrong Credentials"
        }
    ), HTTP_401_UNAUTHORIZED


@auth.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    return jsonify(
        {
            "user": {
                "username": user.username,
                "email": user.email,
            }
        }
    ), HTTP_200_OK


@auth.get("/token/refresh")
@jwt_required(refresh=True)
def refresh_user_token():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)

    return jsonify(
        {
            "access_token": access_token
        }
    ), HTTP_200_OK
