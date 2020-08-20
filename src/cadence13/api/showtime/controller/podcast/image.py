from http import HTTPStatus

import connexion
from flask_jwt_extended import jwt_required
from sqlalchemy.orm.exc import NoResultFound

import cadence13.api.showtime.controller.common.image as common_image
from cadence13.api.showtime.controller.common.image import generate_image_result
from cadence13.api.util.db import db
from cadence13.db.tables import Podcast


@jwt_required
def get_images(podcastId):
    podcast_id = podcastId
    try:
        podcast = db.session.query(Podcast).filter_by(id=podcast_id).one()
    except NoResultFound:
        return connexion.problem(HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase,
                                 'Podcast not found')
    return generate_image_result({
        'rssImage': podcast.rss_image_url,
        'cover': podcast.cover_image_url,
        'background': podcast.background_image_url
    })


@jwt_required
def update_image(podcastId, imageType, body):
    podcast_id = podcastId
    image_type = imageType
    source_url = body['sourceUrl']

    try:
        podcast = db.session.query(Podcast).filter_by(id=podcast_id).one()
    except NoResultFound:
        return connexion.problem(HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase,
                                 'Podcast not found')
    if image_type == 'cover':
        podcast.cover_image_url = source_url
        print('done!')
    elif image_type == 'background':
        podcast.background_image_url = source_url
    db.session.commit()


@jwt_required
def delete_image(podcastId, imageType):
    podcast_id = podcastId
    image_type = imageType
    try:
        podcast = db.session.query(Podcast).filter_by(id=podcast_id).one()
    except NoResultFound:
        return connexion.problem(HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase,
                                 'Podcast not found')
    if image_type is 'cover':
        podcast.cover_image_url = None
    elif image_type is 'background':
        podcast.background_image_url = None
    db.session.commit()


@jwt_required
def create_presigned_post(podcastId, imageType, body):
    podcast_id = podcastId
    image_type = imageType

    try:
        db.session.query(Podcast).filter_by(id=podcast_id).one()
    except NoResultFound:
        return connexion.problem(HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase,
                                 'Podcast not found')

    return common_image.create_presigned_post(
        file_name=body['fileName'],
        content_type=body['contentType'],
        prefix=f'podcasts/{podcast_id}/{image_type}'
    )
