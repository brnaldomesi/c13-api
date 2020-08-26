from http import HTTPStatus

import connexion
from flask_jwt_extended import jwt_required
from sqlalchemy.orm.exc import NoResultFound

import cadence13.api.showtime.controller.common.image as common_image
from cadence13.api.showtime.controller.common.image import generate_image_result
from cadence13.api.util.db import db
from cadence13.db.tables import PodcastCrewMember


@jwt_required
def get_images(crewMemberId):
    crew_member_id = crewMemberId
    try:
        crew_member = db.session.query(PodcastCrewMember).filter_by(id=crew_member_id).one()
    except NoResultFound:
        return connexion.problem(HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase,
                                 'Podcast not found')
    return generate_image_result({'profile': crew_member.profile_image_url}, sizes=[])


@jwt_required
def update_image(crewMemberId, imageType, body):
    crew_member_id = crewMemberId
    image_type = imageType
    source_url = body['sourceUrl']

    try:
        crew_member = db.session.query(PodcastCrewMember).filter_by(id=crew_member_id).one()
    except NoResultFound:
        return connexion.problem(HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase,
                                 'Crew member not found')
    if image_type == 'profile':
        crew_member.profile_image_url = source_url
    db.session.commit()


@jwt_required
def delete_image(crewMemberId, imageType):
    crew_member_id = crewMemberId
    image_type = imageType
    try:
        crew_member = db.session.query(PodcastCrewMember).filter_by(id=crew_member_id).one()
    except NoResultFound:
        return connexion.problem(HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase,
                                 'Crew member not found')
    if image_type == 'profile':
        crew_member.profile_image_url = None
    db.session.commit()


@jwt_required
def create_presigned_post(crewMemberId, imageType, body):
    crew_member_id = crewMemberId
    image_type = imageType

    try:
        db.session.query(PodcastCrewMember.id).filter_by(id=crew_member_id).one()
    except NoResultFound:
        return connexion.problem(HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase,
                                 'Crew member not found')

    return common_image.create_presigned_post(
        file_name=body['fileName'],
        content_type=body['contentType'],
        prefix=f'crew-members/{crew_member_id}/{image_type}'
    )
