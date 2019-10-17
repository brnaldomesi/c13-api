import enum
from base64 import urlsafe_b64encode, urlsafe_b64decode

import msgpack

from cadence13.api.util.logging import get_logger
import time
import operator
import boto3
from sqlalchemy import or_, tuple_
from flask_jwt_extended import jwt_required
from cadence13.api.util.db import db
import cadence13.db.tables as db_tables
from cadence13.db.enums import EpisodeStatus
from cadence13.db.tables import EpisodeNew
from cadence13.api.showtime.schema.api import ApiEpisodeSchema

logger = get_logger(__name__)


@jwt_required
def get_episode(podcastId, episodeId):
    row = (db.session.query(EpisodeNew)
           .filter_by(podcast_id=podcastId)
           .filter_by(id=episodeId)
           .one_or_none())
    schema = ApiEpisodeSchema()
    return schema.dump(row)


@jwt_required
def patch_episode(podcastId, episodeId, body):
    row = (db.session.query(EpisodeNew)
           .filter_by(podcast_id=podcastId)
           .filter_by(id=episodeId)
           .one_or_none())
    if not row:
        return 404, 'Not Found'
    schema = ApiEpisodeSchema()
    print(body)
    deserialized = schema.load(body)
    for k, v in deserialized.items():
        setattr(row, k, v)
    db.session.commit()
    return schema.dump(row)
