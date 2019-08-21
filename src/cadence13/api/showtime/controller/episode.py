from flask_jwt_extended import jwt_required


@jwt_required
def update_episode():
    return 'Not implemented', 501
