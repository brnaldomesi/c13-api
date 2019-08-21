from flask_jwt_extended import jwt_required


@jwt_required
def test_post():
    return {'hello': 'world'}


@jwt_required
def test_get():
    return {'hello': 'world'}
