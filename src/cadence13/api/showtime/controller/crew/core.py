from http import HTTPStatus

import connexion
from flask_jwt_extended import jwt_required


@jwt_required
def create_crew_member(crewMemberId, body):
    return connexion.problem(HTTPStatus.NOT_IMPLEMENTED,
                             HTTPStatus.NOT_IMPLEMENTED.phrase,
                             HTTPStatus.NOT_IMPLEMENTED.phrase)

@jwt_required
def get_crew_member(crewMemberId):
    return connexion.problem(HTTPStatus.NOT_IMPLEMENTED,
                             HTTPStatus.NOT_IMPLEMENTED.phrase,
                             HTTPStatus.NOT_IMPLEMENTED.phrase)

@jwt_required
def patch_crew_member(crewMemberId, body):
    return connexion.problem(HTTPStatus.NOT_IMPLEMENTED,
                             HTTPStatus.NOT_IMPLEMENTED.phrase,
                             HTTPStatus.NOT_IMPLEMENTED.phrase)

@jwt_required
def delete_crew_member(crewMemberId):
    return connexion.problem(HTTPStatus.NOT_IMPLEMENTED,
                             HTTPStatus.NOT_IMPLEMENTED.phrase,
                             HTTPStatus.NOT_IMPLEMENTED.phrase)