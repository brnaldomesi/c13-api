from cadence13.api.util.logging import get_logger
import msgpack
import enum
from base64 import urlsafe_b64decode, urlsafe_b64encode
import operator
from sqlalchemy.orm import relationship
from cadence13.db.tables import (
    Podcast, PodcastConfig, PodcastSocialMedia,
    PodcastSubscription, EpisodeNew, PodcastCategory, PodcastCategoryMap)
from cadence13.db.enums import PodcastStatus, EpisodeStatus
from cadence13.api.util.db import db
from cadence13.api.util.string import underscore_to_camelcase
from cadence13.api.common.schema.api import ApiPodcastSchema, ApiEpisodeSchema

logger = get_logger(__name__)

PODCASTS_DEFAULT_LIMIT = 25
PODCASTS_MAX_LIMIT = 25
EPISODES_DEFAULT_LIMIT = 25
EPISODES_MAX_LIMIT = 100
EPISODE_COLUMNS = [
    EpisodeNew.guid,
    Podcast.guid.label('podcast_guid'),
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


class ApiPodcast(Podcast):
    config = relationship(PodcastConfig)
    categories = relationship(
        PodcastCategory,
        secondary=PodcastCategoryMap.__table__,
        primaryjoin='ApiPodcast.guid == PodcastCategoryMap.podcast_id'
    )


def _encode_podcast_cursor(result_row):
    payload = {
        'title': result_row['title'],
        'guid': result_row['guid']
    }
    packed = msgpack.packb(payload, use_bin_type=True)
    return urlsafe_b64encode(packed).decode('ascii')


def get_podcasts(limit=None, sort_order=None, next_cursor=None, prev_cursor=None):
    limit = limit if limit else EPISODES_DEFAULT_LIMIT
    cursor = next_cursor or prev_cursor
    page_direction = (PageDirection.FORWARD if not cursor or next_cursor
                      else PageDirection.BACKWARD)
    sort_order = SortOrder[sort_order.upper()] if sort_order else SortOrder.ASC
    reverse_order = (SortOrder.ASC if sort_order is SortOrder.DESC
                     else SortOrder.DESC)

    # Base query never changes
    stmt = (db.session.query(ApiPodcast)
            .filter(ApiPodcast.status == PodcastStatus.ACTIVE))

    # Assume this is the first page and use default sort order
    query_order = sort_order
    if cursor:
        cursor = _decode_cursor(cursor)
        # If we're paging backwards, we need to search backwards
        if prev_cursor:
            query_order = reverse_order
        compare_func = operator.lt if query_order is SortOrder.DESC else operator.gt
        compare_cols = (ApiPodcast.title, ApiPodcast.guid)
        compare_vals = (cursor['title'], cursor['guid'])
        stmt = stmt.filter(compare_func(compare_cols, compare_vals))

    # Figure out whether to call desc() or asc() on the fly
    stmt = (stmt.order_by(getattr(ApiPodcast.title, query_order.name.lower())(),
                          getattr(ApiPodcast.guid, query_order.name.lower())()))

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
        'count': len(results),
        'nextCursor': next_cursor,
        'prevCursor': prev_cursor
    }


def get_podcast(podcast_guid):
    row = (db.session.query(ApiPodcast)
           .filter(ApiPodcast.guid == podcast_guid)
           .one_or_none())

    if not row:
        return 'Not found', 404

    schema = ApiPodcastSchema()
    result = schema.dump(row)
    result['socialMedialUrls'] = get_social_media_urls(result['guid'])
    result['subscriptionUrls'] = get_subscription_urls(result['guid'])
    return result


def get_social_media_urls(podcast_guid):
    social_media = (db.session.query(PodcastSocialMedia)
                    .join(Podcast, PodcastSocialMedia.podcast_id == Podcast.id)
                    .filter(Podcast.guid == podcast_guid).all())
    result = {underscore_to_camelcase(s.social_media_service.name): s.social_media_url
              for s in social_media}
    return result


def get_subscription_urls(podcast_guid):
    subscriptions = (db.session.query(PodcastSubscription)
                     .join(Podcast, PodcastSubscription.podcast_id == Podcast.id)
                     .filter(Podcast.guid == podcast_guid).all())
    result = {underscore_to_camelcase(s.subscription_service.name): s.subscription_url
              for s in subscriptions}
    return result


def get_image_urls(podcast_guid):
    return []


def _decode_cursor(encoded_cursor):
    return msgpack.unpackb(urlsafe_b64decode(encoded_cursor), raw=False)


def _encode_episode_cursor(result_row):
    payload = {
        'published_at': result_row['publishedAt'],
        'guid': result_row['guid']
    }
    packed = msgpack.packb(payload, use_bin_type=True)
    return urlsafe_b64encode(packed).decode('ascii')


def get_episodes(podcast_guid, limit=None, sort_order=None,
                 next_cursor=None, prev_cursor=None):
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
            .filter(Podcast.guid == podcast_guid)
            .filter(EpisodeNew.status == EpisodeStatus.ACTIVE)
            .filter(EpisodeNew.published_at != None))

    # Assume this is the first page and use default sort order
    query_order = sort_order
    if cursor:
        cursor = _decode_cursor(cursor)
        # If we're paging backwards, we need to search backwards
        if prev_cursor:
            query_order = reverse_order
        compare_func = operator.lt if query_order is SortOrder.DESC else operator.gt
        compare_cols = (EpisodeNew.published_at, EpisodeNew.guid)
        compare_vals = (cursor['published_at'], cursor['guid'])
        stmt = stmt.filter(compare_func(compare_cols, compare_vals))

    # Figure out whether to call desc() or asc() on the fly
    stmt = (stmt.order_by(getattr(EpisodeNew.published_at, query_order.name.lower())(),
                          getattr(EpisodeNew.guid, query_order.name.lower())()))

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
        'count': len(results),
        'nextCursor': next_cursor,
        'prevCursor': prev_cursor
    }


# def get_crew_members(podcast_guid):
#     rows = (db.session.query(PodcastStaffer, Staffer)
#             .join(Staffer, PodcastStaffer.staffer_id == Staffer.id)
#             .join(Podcast, Podcast.id == PodcastStaffer.podcast_id)
#             .filter(Podcast.guid == podcast_guid)
#             .order_by(PodcastStaffer.sort_no).all())
#     return [{
#         'staffer_guid': staffer.guid,
#         'first_name': staffer.first_name,
#         'middle_name': staffer.middle_name,
#         'last_name': staffer.last_name,
#         'biography': staffer.biography,
#         'image_url': staffer.image_url,
#         'sort_no': podcast_staffer.sort_no
#     } for podcast_staffer, staffer in rows]
