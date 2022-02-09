from flask import Flask, redirect, jsonify
import os

from constants.http_status_codes import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from src.auth import auth
from src.bookmark import bookmarks
from src.database import db, Bookmark
from flask_jwt_extended import JWTManager


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SECRET_KEY"),
            SQLALCHEMY_DB_URI=os.environ.get("SQLALCHEMY_DB_URI"),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY")
        )
    else:
        app.config.from_mapping(test_config)

    JWTManager(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookmarks.db'
    db.init_app(app)
    app.register_blueprint(auth)
    app.register_blueprint(bookmarks)

    @app.get("/<short_url>")
    def redirect_url(short_url):
        bookmark_for_url = Bookmark.query.filter_by(short_url=short_url).first_or_404()

        bookmark_for_url.visits = bookmark_for_url.visits + 1
        db.session.commit()

        return redirect(bookmark_for_url.url)

    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def error_handler(e):
        return jsonify(
            {
                "error": "There's an error with the server, please try again later"
            }
        )

    return app
