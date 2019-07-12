from cadence13.api.util.logging import get_logger
from flask import jsonify, request
from flask_jwt_extended import (
    get_csrf_token, create_access_token, create_refresh_token,
    get_jwt_identity, set_access_cookies, set_refresh_cookies,
    unset_jwt_cookies, jwt_refresh_token_required
)

logger = get_logger(__name__)


def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if username != 'test' or password != 'test':
        return jsonify({'login': False}), 401

    # Create the tokens we will be sending back to the user
    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)

    # Return the double submit values in the resulting JSON
    resp = jsonify({
        'accessCsrf': get_csrf_token(access_token),
        'refreshCsrf': get_csrf_token(refresh_token)
    })

    # Set the JWT in the cookies
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)
    return resp, 200


@jwt_refresh_token_required
def refresh():
    # Create the new access token
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    resp = jsonify({
        'accessCsrf': get_csrf_token(access_token),
    })
    set_access_cookies(resp, access_token)
    return resp, 200


# Because the JWTs are stored in an httponly cookie now, we cannot
# log the user out by simply deleting the cookie in the frontend.
# We need the backend to send us a response to delete the cookies
# in order to logout. unset_jwt_cookies is a helper function to
# do just that.
def logout():
    resp = jsonify({'logout': True})
    unset_jwt_cookies(resp)
    return resp, 200
