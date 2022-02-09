from flask import Blueprint, request, jsonify
import validators
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.database import Bookmark, db

from constants.http_status_codes import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT, HTTP_200_OK, HTTP_404_NOT_FOUND, \
    HTTP_204_NO_CONTENT

bookmarks = Blueprint("bookmarks", __name__, url_prefix="/api/v1/bookmarks")


@bookmarks.route("/", methods=["GET", "POST"])
@jwt_required()
def bookmarks_handler():
    current_user = get_jwt_identity()

    if request.method == "POST":
        body = request.json.get("body", "")
        url = request.json.get("url", "")

        if not validators.url(url):
            return jsonify(
                {
                    "error": "Enter a valid URL"
                }
            ), HTTP_400_BAD_REQUEST

        if Bookmark.query.filter_by(url=url).first():
            return jsonify(
                {
                    "error": "URL already exists"
                }
            ), HTTP_409_CONFLICT

        bookmark = Bookmark(body=body, url=url, user_id=current_user)
        db.session.add(bookmark)
        db.session.commit()

        return jsonify(
            {
                "id": bookmark.id,
                "url": bookmark.url,
                "short_url": bookmark.short_url,
                "body": bookmark.body,
                "visits": bookmark.visits,
                "created_at": bookmark.created_at,
                "updated_at": bookmark.updated_at
            }
        ), HTTP_200_OK

    else:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 5, type=int)

        user_bookmark = Bookmark.query.filter_by(user_id=current_user). \
            paginate(page, per_page)

        meta = {
            "page": user_bookmark.page,
            "per_page": user_bookmark.per_page,
            "pages": user_bookmark.pages,
            "has_next": user_bookmark.has_next,
            "has_prev": user_bookmark.has_prev,
            "total": user_bookmark.total,
        }
        data = []

        for bookmark in user_bookmark.items:
            data.append({
                "id": bookmark.id,
                "url": bookmark.url,
                "short_url": bookmark.short_url,
                "body": bookmark.body,
                "visits": bookmark.visits,
                "created_at": bookmark.created_at,
                "updated_at": bookmark.updated_at
            })

        return jsonify({
            "metadata": meta,
            "data": data
        }), HTTP_200_OK


@bookmarks.get("/<int:bookmark_id>")
@jwt_required()
def get_bookmark(bookmark_id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user, id=bookmark_id).first()

    if not bookmark:
        return jsonify(
            {
                "message": "Bookmark not found"
            }
        ), HTTP_404_NOT_FOUND

    return jsonify(
        {
            "id": bookmark.id,
            "url": bookmark.url,
            "short_url": bookmark.short_url,
            "body": bookmark.body,
            "visits": bookmark.visits,
            "created_at": bookmark.created_at,
            "updated_at": bookmark.updated_at
        }
    )


@bookmarks.patch("/<int:bookmark_id>")
@jwt_required()
def edit_bookmark(bookmark_id):
    url = request.json.get("url", "")
    body = request.json.get("body", "")

    if not validators.url(url):
        return jsonify(
            {
                "error": "Enter a valid URL"
            }
        ), HTTP_400_BAD_REQUEST

    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user, id=bookmark_id).first()

    if not bookmark:
        return jsonify(
            {
                "message": "Bookmark not found"
            }
        ), HTTP_404_NOT_FOUND

    bookmark.url = url
    bookmark.body = body
    db.session.commit()

    return jsonify(
        {
            "id": bookmark.id,
            "url": bookmark.url,
            "short_url": bookmark.short_url,
            "body": bookmark.body,
            "visits": bookmark.visits,
            "created_at": bookmark.created_at,
            "updated_at": bookmark.updated_at
        }
    ), HTTP_200_OK


@bookmarks.delete("/<int:bookmark_id>")
@jwt_required()
def delete_bookmark(bookmark_id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user, id=bookmark_id).first()

    if not bookmark:
        return jsonify(
            {
                "message": "Bookmark not found"
            }
        ), HTTP_404_NOT_FOUND

    db.session.delete(bookmark)
    db.session.commit()

    return jsonify(
        {}
    ), HTTP_204_NO_CONTENT


@bookmarks.get("/stats")
@jwt_required()
def bookmark_stats():
    current_user = get_jwt_identity()

    data = []

    user_bookmarks = Bookmark.query.filter_by(user_id=current_user).all()

    for bookmark in user_bookmarks:
        data.append(
            {
                "url": bookmark.url,
                "short_url": bookmark.short_url,
                "body": bookmark.body,
                "visits": bookmark.visits
            }
        )

    return jsonify(data), HTTP_200_OK
