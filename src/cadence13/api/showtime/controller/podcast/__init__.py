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
from cadence13.db.enums import PodcastStatus, EpisodeStatus
from cadence13.db.tables import Podcast, PodcastConfig, PodcastCrewMember, EpisodeNew
from cadence13.api.showtime.schema.db import PodcastCrewMemberSchema
from cadence13.api.showtime.schema.api import (ApiPodcastSchema, ApiPodcastConfigSchema,
                                               PodcastSubscriptionSchema, PodcastSocialMediaSchema,
                                               ApiEpisodeSchema)
import cadence13.api.showtime.model.podcast.subscription as subscription_model
import cadence13.api.showtime.model.podcast.social_media as social_media_model
from cadence13.api.showtime.db.table import ApiPodcast
from cadence13.db.tables import Podcast

logger = get_logger(__name__)


@jwt_required
def search_podcasts(search=None, limit=None):
    if search is None:
        return []
    limit = limit if limit else PODCASTS_DEFAULT_LIMIT
    # Base query never changes
    stmt = (db.session.query(Podcast)
            .filter(Podcast.status == PodcastStatus.ACTIVE))

    search_like = '%{}%'.format(search)
    podcasts = stmt.filter(or_(Podcast.title.ilike(search_like),
                           Podcast.subtitle.ilike(search_like),
                           Podcast.summary.ilike(search_like))) \
               .order_by(Podcast.title.asc()) \
               .limit(limit).all()
    results = [{
        'id': podcast.id,
        'slug': podcast.slug,
        'title': podcast.title,
        'subtitle': podcast.subtitle,
        'updatedAt': podcast.updated_at,
        'imageUrl': podcast.image_url,
        'author': podcast.author,
        'summary': podcast.summary,
    } for podcast in podcasts]
    return results


@jwt_required
def get_podcasts(search=None, limit=None, sortOrder=None, nextCursor=None, prevCursor=None):
    # Naming convention housekeeping
    sort_order = sortOrder
    next_cursor = nextCursor
    prev_cursor = prevCursor

    limit = limit if limit else PODCASTS_DEFAULT_LIMIT
    cursor = next_cursor or prev_cursor
    page_direction = (PageDirection.FORWARD if not cursor or next_cursor
                      else PageDirection.BACKWARD)
    sort_order = SortOrder[sort_order.upper()] if sort_order else SortOrder.ASC
    reverse_order = (SortOrder.ASC if sort_order is SortOrder.DESC
                     else SortOrder.DESC)

    # Base query never changes
    stmt = (db.session.query(ApiPodcast)
            .filter(ApiPodcast.status == PodcastStatus.ACTIVE))

    if search is not None:
        search_like = '%{}%'.format(search)
        stmt = stmt.filter(or_(ApiPodcast.title.ilike(search_like),
                               ApiPodcast.subtitle.ilike(search_like),
                               ApiPodcast.summary.ilike(search_like)))

    # TODO: Add any filters

    # Fetch total results before pagination and limits
    total = stmt.count()

    # Handle any pagination here. Assume this is
    # the first page and use default sort order
    query_order = sort_order
    if cursor:
        cursor = _decode_cursor(cursor)
        # If we're paging backwards, we need to search backwards
        if prev_cursor:
            query_order = reverse_order
        compare_func = operator.lt if query_order is SortOrder.DESC else operator.gt
        compare_cols = tuple_(ApiPodcast.title, ApiPodcast.id)
        compare_vals = tuple_(cursor['title'], cursor['id'])
        stmt = stmt.filter(compare_func(compare_cols, compare_vals))

    # Figure out whether to call desc() or asc() on the fly
    stmt = (stmt.order_by(getattr(ApiPodcast.title, query_order.name.lower())(),
                          getattr(ApiPodcast.id, query_order.name.lower())()))

    # Fetch an extra row to see if there's more to get
    query_limit = limit + 1
    stmt = stmt.limit(query_limit)

    # Finally perform the query
    rows = stmt.all()
    has_more = len(rows) == query_limit
    if has_more:
        del rows[-1]
    if query_order != sort_order:
        rows.reverse()

    schema = ApiPodcastSchema(many=True)
    results = schema.dump(rows)

    has_next = prev_cursor or (page_direction is PageDirection.FORWARD and has_more)
    has_prev = next_cursor or (page_direction is PageDirection.BACKWARD and has_more)
    next_cursor = None
    prev_cursor = None

    if has_next:
        next_cursor = _encode_podcast_cursor(results[-1])
    if has_prev:
        prev_cursor = _encode_podcast_cursor(results[0])

    return {
        'data': results,
        'total': total,
        'nextCursor': next_cursor,
        'prevCursor': prev_cursor
    }


@jwt_required
def get_podcast(podcastId):
    row = (db.session.query(ApiPodcast)
           .filter(ApiPodcast.id == podcastId)
           .one_or_none())
    if not row:
        return 'Not found', 404
    schema = ApiPodcastSchema()
    result = schema.dump(row)
    result['socialMedialUrls'] = get_social_media_urls(result['id'])
    result['subscriptionUrls'] = get_subscription_urls(result['id'])
    return result


@jwt_required
def update_podcast(podcastId, body: dict):
    # Remove config from the body so it can be processed separately.
    config = body.pop('config', None)

    if body:
        schema = ApiPodcastSchema()
        deserialized = schema.load(body)
        logger.info(deserialized)
        # FIXME: check for schema validation errors

        row = (db.session.query(Podcast)
               .filter_by(id=podcastId)
               .one_or_none())
        if not row:
            return 'Not found', 404
        for k, v in deserialized.items():
            if hasattr(row, k):
                setattr(row, k, v)
        db.session.commit()

    if config:
        update_podcast_config(podcastId, config)

    return get_podcast(podcastId)


@jwt_required
def get_podcast_config(podcastId):
    stmt = (db.session.query(db_tables.PodcastConfig)
            .join(db_tables.Podcast, db_tables.PodcastConfig.id == db_tables.Podcast.podcast_config_id)
            .filter(Podcast.id == podcastId))
    row = stmt.one_or_none()
    if not row:
        return 'Not Found', 404
    schema = ApiPodcastConfigSchema()
    return schema.dump(row)


@jwt_required
def update_podcast_config(podcastId, body):
    schema = ApiPodcastConfigSchema()
    deserialized = schema.load(body)
    stmt = (db.session.query(db_tables.PodcastConfig)
            .join(db_tables.Podcast, db_tables.PodcastConfig.id == db_tables.Podcast.podcast_config_id)
            .filter(Podcast.id == podcastId))
    row = stmt.one_or_none()
    if not row:
        return 'Not Found', 404
    for k, v in deserialized.items():
        setattr(row, k, v)
    db.session.commit()
    return schema.dump(row)


@jwt_required
def get_episodes(podcastId, limit=None, sortOrder=None,
                 nextCursor=None, prevCursor=None):
    # Naming convention housekeeping
    podcast_id = podcastId
    sort_order = sortOrder
    next_cursor = nextCursor
    prev_cursor = prevCursor

    limit = limit if limit else EPISODES_DEFAULT_LIMIT
    cursor = next_cursor or prev_cursor
    page_direction = (PageDirection.FORWARD if not cursor or next_cursor
                      else PageDirection.BACKWARD)
    sort_order = SortOrder[sort_order.upper()] if sort_order else SortOrder.DESC
    reverse_order = (SortOrder.ASC if sort_order is SortOrder.DESC
                     else SortOrder.DESC)

    # Base query never changes
    stmt = (db.session.query(*EPISODE_COLUMNS)
            .join(Podcast, EpisodeNew.podcast_id == Podcast.id)
            .filter(Podcast.id == podcast_id)
            .filter(EpisodeNew.status == EpisodeStatus.ACTIVE)
            .filter(EpisodeNew.published_at != None))

    total = stmt.count()

    # Assume this is the first page and use default sort order
    query_order = sort_order
    if cursor:
        cursor = _decode_cursor(cursor)
        # If we're paging backwards, we need to search backwards
        if prev_cursor:
            query_order = reverse_order
        compare_func = operator.lt if query_order is SortOrder.DESC else operator.gt
        compare_cols = tuple_(EpisodeNew.published_at, EpisodeNew.id)
        compare_vals = tuple_(cursor['published_at'], cursor['id'])
        stmt = stmt.filter(compare_func(compare_cols, compare_vals))

    # Figure out whether to call desc() or asc() on the fly
    stmt = (stmt.order_by(getattr(EpisodeNew.published_at, query_order.name.lower())(),
                          getattr(EpisodeNew.id, query_order.name.lower())()))

    # Fetch an extra row to see if there's more to get
    query_limit = limit + 1
    stmt = stmt.limit(query_limit)

    # Finally perform the query
    episodes = stmt.all()
    has_more = len(episodes) == query_limit
    if has_more:
        del episodes[-1]
    if query_order != sort_order:
        episodes.reverse()

    schema = ApiEpisodeSchema(many=True)
    results = schema.dump(episodes)

    has_next = prev_cursor or (page_direction is PageDirection.FORWARD and has_more)
    has_prev = next_cursor or (page_direction is PageDirection.BACKWARD and has_more)
    next_cursor = None
    prev_cursor = None

    if has_next:
        next_cursor = _encode_episode_cursor(results[-1])
    if has_prev:
        prev_cursor = _encode_episode_cursor(results[0])

    return {
        'data': results,
        'total': total,
        'nextCursor': next_cursor,
        'prevCursor': prev_cursor
    }


@jwt_required
def assign_network():
    return 'Not implemented', 501


@jwt_required
def get_subscription_urls(podcastId):
    rows = subscription_model.get_subscription_urls(db.session, podcastId)
    result = {r.field_name: r.subscription_url for r in rows}
    result['lockedSyncFields'] = [r.field_name for r in rows if r.disable_sync]
    return result


@jwt_required
def patch_subscription_urls(podcastId, body):
    locked = set(body.pop('lockedSyncFields', []))
    subscription_model.update_locked_sync_fields(
        db.session, podcastId, locked)

    fields = locked.union(body.keys())
    patchable = {f: {'field_name': f} for f in fields}
    for field, url in body.items():
        patchable[field]['subscription_url'] = url
    serialized = patchable.values()
    schema = PodcastSubscriptionSchema(many=True)
    deserialized = schema.load(serialized)
    for subscription in deserialized:
        subscription_model.update_subscription(db.session, podcastId, subscription)
    return get_subscription_urls(podcastId)


@jwt_required
def get_social_media_urls(podcastId):
    rows = social_media_model.get_social_media_urls(db.session, podcastId)
    result = {r.field_name: r.social_media_url for r in rows}
    result['lockedSyncFields'] = [r.field_name for r in rows if r.disable_sync]
    return result


@jwt_required
def patch_social_media_urls(podcastId, body):
    locked = set(body.pop('lockedSyncFields', []))
    social_media_model.update_locked_sync_fields(
        db.session, podcastId, locked)

    fields = locked.union(body.keys())
    patchable = {f: {'field_name': f} for f in fields}
    for field, url in body.items():
        patchable[field]['subscription_url'] = url
    serialized = patchable.values()
    schema = PodcastSocialMediaSchema(many=True)
    deserialized = schema.load(serialized)
    for social_media in deserialized:
        social_media_model.update_social_media(db.session, podcastId, social_media)
    return get_subscription_urls(podcastId)


@jwt_required
def get_crew_members(podcastId):
    rows = (db.session.query(PodcastCrewMember)
            .filter_by(podcast_id=podcastId)
            .filter_by(deleted=False)
            .order_by(PodcastCrewMember.sort_order.asc()).all())
    schema = PodcastCrewMemberSchema(many=True)
    return schema.dump(rows)


@jwt_required
def get_crew_member(podcastId, crewMemberId):
    row = (db.session.query(PodcastCrewMember)
           .filter_by(podcast_id=podcastId)
           .filter_by(id=crewMemberId)
           .filter_by(deleted=False)
           .one_or_none())
    schema = PodcastCrewMemberSchema()
    return schema.dump(row)


@jwt_required
def create_crew_member(podcastId, body):
    stmt = (db.session.query(Podcast)
            .filter_by(id=podcastId)
            .exists())
    exists = db.session.query(stmt).scalar()
    if not exists:
        return 'Podcast ID {} does not exist'.format(podcastId), 404

    schema = PodcastCrewMemberSchema()
    deserialized = schema.load(body)
    row = PodcastCrewMember(podcast_id=podcastId, **deserialized)
    db.session.add(row)
    db.session.commit()


@jwt_required
def patch_crew_member(podcastId, crewMemberId, body):
    row = (db.session.query(PodcastCrewMember)
           .filter_by(podcast_id=podcastId)
           .filter_by(id=crewMemberId)
           .one_or_none())
    if not row:
        return 404, 'Not Found'
    schema = PodcastCrewMemberSchema()
    deserialized = schema.load(body)
    for k, v in deserialized.items():
        setattr(row, k, v)
    db.session.commit()


@jwt_required
def delete_crew_member(podcastId, crewMemberId):
    row = (db.session.query(PodcastCrewMember)
           .filter_by(podcast_id=podcastId)
           .filter_by(id=crewMemberId)
           .one_or_none())
    if not row:
        return 404, 'Not Found'
    row.deleted = True
    db.session.commit()


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


PODCASTS_DEFAULT_LIMIT = 25
PODCASTS_MAX_LIMIT = 25
EPISODES_DEFAULT_LIMIT = 25
EPISODES_MAX_LIMIT = 100
EPISODE_COLUMNS = [
    EpisodeNew.id,
    Podcast.id.label('podcast_id'),
    EpisodeNew.season_no,
    EpisodeNew.episode_no,
    EpisodeNew.title,
    EpisodeNew.subtitle,
    EpisodeNew.summary,
    EpisodeNew.author,
    EpisodeNew.episode_type,
    EpisodeNew.image_url,
    EpisodeNew.audio_url,
    EpisodeNew.is_explicit,
    EpisodeNew.published_at,
    EpisodeNew.status,
    EpisodeNew.created_at,
    EpisodeNew.updated_at
]


class SortOrder(enum.Enum):
    DESC: str = 'desc'
    ASC: str = 'asc'


class PageDirection(enum.Enum):
    FORWARD = enum.auto()
    BACKWARD = enum.auto()


def _encode_podcast_cursor(result_row):
    payload = {
        'title': result_row['title'],
        'id': result_row['id']
    }
    packed = msgpack.packb(payload, use_bin_type=True)
    return urlsafe_b64encode(packed).decode('ascii')


def _decode_cursor(encoded_cursor):
    return msgpack.unpackb(urlsafe_b64decode(encoded_cursor), raw=False)


def _encode_episode_cursor(result_row):
    payload = {
        'published_at': result_row['publishedAt'],
        'id': result_row['id']
    }
    packed = msgpack.packb(payload, use_bin_type=True)
    return urlsafe_b64encode(packed).decode('ascii')