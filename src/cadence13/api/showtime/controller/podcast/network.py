from http import HTTPStatus

import connexion
from flask_jwt_extended import jwt_required

from cadence13.api.util.db import db
from cadence13.db.tables import Podcast, Network


@jwt_required
def update_podcast_network(podcastId, body: dict):
    podcast_id = podcastId  # just for aesthetics
    network_id = body['networkId']
    podcast = db.session.query(Podcast).filter_by(id=podcast_id).one_or_none()
    if not podcast:
        return connexion.problem(HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase, 'Podcast not found')
    if podcast.network_id == network_id:
        return HTTPStatus.NO_CONTENT.phrase, HTTPStatus.NO_CONTENT

    network = db.session.query(Network).filter_by(id=network_id).one_or_none()
    if not network:
        return connexion.problem(HTTPStatus.BAD_REQUEST, HTTPStatus.BAD_REQUEST.phrase, 'Network not found')

    podcast.network_id = network_id
    db.session.commit()
    return HTTPStatus.NO_CONTENT.phrase, HTTPStatus.NO_CONTENT
