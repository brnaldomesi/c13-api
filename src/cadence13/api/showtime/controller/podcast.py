from cadence13.api.util.logging import get_logger
import time
import boto3
from sqlalchemy import and_
from flask_jwt_extended import jwt_required
from cadence13.api.util.db import db
import cadence13.db.tables as db_tables
from cadence13.db.tables import Podcast, PodcastCrewMember
import cadence13.api.common.controller.podcast as common_podcast
from cadence13.api.common.schema.db import PodcastConfigSchema, PodcastCrewMemberSchema
from cadence13.api.common.schema.api import ApiPodcastSchema, PodcastSubscriptionSchema
import cadence13.api.common.model.podcast.subscription as podcast_subscription_model

logger = get_logger(__name__)


@jwt_required
def get_podcasts(limit=None, sortOrder=None, nextCursor=None, prevCursor=None):
    return common_podcast.get_podcasts(
        limit=limit,
        sort_order=sortOrder,
        next_cursor=nextCursor,
        prev_cursor=prevCursor)


@jwt_required
def get_podcast(podcastId):
    return common_podcast.get_podcast(podcastId)


@jwt_required
def update_podcast(podcastId, body: dict):
    schema = ApiPodcastSchema()
    deserialized = schema.load(body)
    logger.info(deserialized)
    # FIXME: check for schema validation errors

    # if deserialized['config']:
    #     _update_podcast_config(podcastId, deserialized['config'])

    row = (db.session.query(Podcast)
           .filter_by(guid=podcastId)
           .one_or_none())

    if not row:
        return 'Not found', 404

    for k, v in deserialized.items():
        if hasattr(row, k):
            setattr(row, k, v)

    db.session.commit()
    return get_podcast(podcastId)


# def _create_podcast_config(podcast_guid, params: dict):
#     select_stmt = (db.session.query(Podcast.id)
#                    .filter_by(guid=podcast_guid))
#     row = PodcastConfig(podcast_id=select_stmt)
#     for k, v in params.items():
#         if hasattr(row, k):
#             setattr(row, k, v)
#     db.session.add(row)
#     db.session.commit()
#
#     schema = PodcastConfigSchema()
#     return schema.dump(row)


# def _update_podcast_config(podcast_guid, params):
#     logger.info(podcast_guid)
#     logger.info(params)
#
#     row = (db.session.query(PodcastConfig)
#            .join(Podcast, PodcastConfig.podcast_id == Podcast.id)
#            .filter(Podcast.guid == podcast_guid)
#            .one_or_none())
#
#     if not row:
#         logger.info('creating config for {}'.format(podcast_guid))
#         return _create_podcast_config(podcast_guid, params)
#
#     for k, v in params.items():
#         if hasattr(row, k):
#             logger.info('adding {} to update fields'.format(k))
#             setattr(row, k, v)
#
#     schema = PodcastConfigSchema()
#     return schema.dump(row)


# @jwt_required
# def update_locked_sync_fields(podcastId, body):
#     normalized = frozenset([field.lower() for field in body])
#     podcast_config = _update_podcast_config(podcastId, {
#         'locked_sync_fields': normalized
#     })
#     return podcast_config['locked_sync_fields']


# @jwt_required
# def update_podcast_tags(podcastId, body):
#     normalized = frozenset([tag.lower() for tag in body])
#     podcast_config = _update_podcast_config(podcastId, {
#         'tags': normalized
#     })
#     return podcast_config['tags']


@jwt_required
def get_episodes(podcastId, limit=None, sortOrder=None,
                 nextCursor=None, prevCursor=None):
    return common_podcast.get_episodes(
        podcast_guid=podcastId,
        limit=limit,
        sort_order=sortOrder,
        next_cursor=nextCursor,
        prev_cursor=prevCursor
    )


@jwt_required
def assign_network():
    return 'Not implemented', 501


@jwt_required
def get_subscription_urls(podcastId):
    stmt = (db.session.query(
                db_tables.SubscriptionService.field_name,
                db_tables.PodcastSubscriptionMap.subscription_url,
                db_tables.PodcastSubscriptionMap.disable_sync,
                db_tables.PodcastSubscriptionMap.deleted
            )
            .outerjoin(db_tables.PodcastSubscriptionMap, and_(
                db_tables.PodcastSubscriptionMap.subscription_service_id == db_tables.SubscriptionService.id,
                db_tables.PodcastSubscriptionMap.podcast_id == podcastId
            ))
            .filter(db_tables.SubscriptionService.is_active == True))
    rows = stmt.all()
    result = {r.field_name: r.subscription_url for r in rows}
    result['lockedSyncFields'] = [r.field_name for r in rows if r.disable_sync]
    return result


@jwt_required
def patch_subscription_urls(podcastId, body):
    locked = set(body.pop('lockedSyncFields', []))
    podcast_subscription_model.update_locked_sync_fields(
        db.session, podcastId, locked)

    fields = locked.union(body.keys())
    patchable = {f: {'field_name': f} for f in fields}
    for field, url in body.items():
        patchable[field]['subscription_url'] = url
    serialized = patchable.values()
    logger.info(serialized)
    schema = PodcastSubscriptionSchema(many=True)
    deserialized = schema.load(serialized)
    for subscription in deserialized:
        podcast_subscription_model.update_subscription(db.session, podcastId, subscription)
    return get_subscription_urls(podcastId)


@jwt_required
def get_social_media_urls(podcastId):
    return {
        'facebook': 'https://www.facebook.com/podsaveamerica/',
        'instagram': None,
        'pinterest': None,
        'reddit': None,
        'twitter': 'https://twitter.com/PodSaveAmerica',
        'locked': [
            'facebook'
        ]
    }


@jwt_required
def patch_social_media_urls(podcastId, body):
    response = {
        'facebook': 'https://www.facebook.com/podsaveamerica/',
        'instagram': None,
        'pinterest': None,
        'reddit': None,
        'twitter': 'https://twitter.com/PodSaveAmerica',
        'locked': [
            'facebook'
        ]
    }
    for k, v in body.items():
        if k in response:
            response[k] = v
    return response


@jwt_required
def get_crew_members(podcastId):
    return common_podcast.get_crew_members(podcastId)


@jwt_required
def create_crew_member(podcastId, body):
    schema = PodcastCrewMemberSchema()
    deserialized = schema.load(body)
    row = PodcastCrewMember(podcast_id=podcastId, **deserialized)
    db.session.add(row)
    db.session.commit()


@jwt_required
def delete_crew_member(podcastId, crewMemberId):
    row = (db.session.query(PodcastCrewMember)
           .filter_by(podcast_id=podcastId)
           .filter_by(id=crewMemberId)
           .one_or_none())
    if not row:
        return 404, 'Not Found'
    db.session.delete(row)


@jwt_required
def create_image_upload_url(podcastId):
    # s3 = boto3.client('s3',
    #   aws_access_key_id='',
    #   aws_secret_access_key=''
    # )
    s3 = boto3.client('s3')
    key = 'podcasts/{}/{}/original.jpg'.format(podcastId, int(time.time()))
    return s3.generate_presigned_post(
        Bucket='cadence13-showtime-upload-test',
        Key=key,
        Conditions=[
            {'acl': 'public-read'},
            {'Content-Type': 'image/jpeg'}
        ],
        ExpiresIn=600
    )
