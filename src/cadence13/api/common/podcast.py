from typing import List
import operator
from marshmallow import Schema, fields, post_dump, pre_dump
from cadence13.db.tables import (
    Podcast, PodcastConfig, PodcastSocialMedia,
    PodcastSubscription, EpisodeNew)
from cadence13.db.enums import PodcastStatus, EpisodeStatus
from cadence13.api.util.db import db
from cadence13.api.util.string import underscore_to_camelcase
from cadence13.api.common.schema import PodcastSchema, PodcastConfigSchema, EpisodeSchema

PODCASTS_LIMIT = 25
EPISODES_LIMIT = 25


class CustomPodcastSchema(Schema):
    podcast = fields.Nested(PodcastSchema(), attribute='Podcast')
    podcast_config = fields.Nested(PodcastConfigSchema(), attribute='PodcastConfig')

    @pre_dump(pass_many=False)
    def fill_missing_config(self, data, many, **kwargs):
        if not data.PodcastConfig:
            return {
                'Podcast': data.Podcast,
                'PodcastConfig': {
                    'tags': [],
                    'locked_sync_fields': []
                }
            }
        return data

    @post_dump(pass_many=False)
    def merge_table(self, data, many, **kwargs):
        podcast = data['podcast']
        if data['podcast_config'] is not None:
            podcast.update(data['podcast_config'])
        return podcast


def get_podcasts(start_after=None, ending_before=None, limit=PODCASTS_LIMIT):
    title = None
    podcast_guid = start_after or ending_before
    sort_order = 'asc'
    page_size = limit + 1

    if podcast_guid:
        title = (db.session.query(Podcast.title)
                 .filter(Podcast.guid == podcast_guid)
                 .scalar())

    stmt = (db.session.query(Podcast, PodcastConfig)
            .outerjoin(PodcastConfig, Podcast.id == PodcastConfig.podcast_id)
            .filter(Podcast.status == PodcastStatus.ACTIVE))
    if start_after and title:
        stmt = stmt.filter((Podcast.title, Podcast.guid) > (title, podcast_guid))
    elif ending_before and title:
        stmt = stmt.filter((Podcast.title, Podcast.guid) < (title, podcast_guid))
        sort_order = 'desc'
    stmt = (stmt.order_by(getattr(Podcast.title, sort_order)(),
                          getattr(Podcast.guid, sort_order)())
            .limit(page_size))

    rows = stmt.all()
    schema = CustomPodcastSchema(many=True)
    results = schema.dump(rows)

    has_more = len(results) == page_size
    if has_more:
        del results[-1]

    next_start_after = None
    next_ending_before = None
    if start_after:
        if results:
            next_ending_before = results[0]['guid']
        if has_more:
            next_start_after = results[-1]['guid']
    elif ending_before:
        if results:
            next_start_after = results[0]['guid']
        if has_more:
            next_ending_before = results[-1]['guid']
    elif has_more:
        next_start_after = results[-1]['guid']

    if 'desc' == sort_order and isinstance(results, list):
        results.sort(key=lambda x: x['title'])

    links = {}
    if next_start_after:
        links['next'] = '/podcasts?limit={}&startAfter={}'.format(limit, next_start_after)
    if next_ending_before:
        links['prev'] = '/podcasts?limit={}&endingBefore={}'.format(limit, next_ending_before)

    return {
        'results': results,
        'count': len(results),
        'hasMore': has_more,
        'links': links
    }


def get_podcast(podcast_guid):
    row = (db.session.query(Podcast, PodcastConfig)
           .outerjoin(PodcastConfig, Podcast.id == PodcastConfig.podcast_id)
           .filter(Podcast.guid == podcast_guid)
           .one_or_none())

    if not row:
        return 'Not found', 404

    schema = CustomPodcastSchema()
    result = schema.dump(row)
    result['socialMedialUrls'] = get_social_media_urls(result['guid'])
    result['subscriptionUrls'] = get_subscription_urls(result['guid'])
    return result


def update_podcast(podcast_guid, body: dict):
    schema = PodcastSchema()
    columns = schema.load(body)

    #FIXME: check for schema validation errors

    row = (db.session.query(Podcast)
           .filter_by(guid=podcast_guid)
           .one_or_none())

    if not row:
        return 'Not found', 404

    for k, v in columns.items():
        if hasattr(row, k):
            setattr(row, k, v)

    db.session.commit()
    return get_podcast(podcast_guid)


def _create_podcast_config(podcast_guid, params: dict):
    select_stmt = (db.session.query(Podcast.id)
                   .filter_by(guid=podcast_guid))
    row = PodcastConfig(podcast_id=select_stmt)
    for k, v in params.items():
        if hasattr(row, k):
            setattr(row, k, v)
    db.session.add(row)
    db.session.commit()

    schema = PodcastConfigSchema()
    return schema.dump(row)


def _update_podcast_config(podcast_guid, params):
    row = (db.session.query(PodcastConfig)
           .join(Podcast, PodcastConfig.podcast_id == Podcast.id)
           .filter(Podcast.guid == podcast_guid)
           .one_or_none())

    if not row:
        return _create_podcast_config(podcast_guid, params)

    for k, v in params.items():
        if hasattr(row, k):
            setattr(row, k, v)

    schema = PodcastConfigSchema()
    return schema.dump(row)


def update_locked_sync_fields(podcast_guid, fields: List[str]):
    normalized = frozenset([f.lower() for f in fields])
    podcast_config = _update_podcast_config(podcast_guid, {
        'locked_sync_fields': normalized
    })
    return podcast_config['locked_sync_fields']


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


def get_episodes(podcast_guid, start_after=None, ending_before=None,
                 limit=EPISODES_LIMIT, sort_order='desc'):
    published_at = None
    episode_guid = start_after or ending_before
    page_size = limit + 1
    reverse_order = 'asc' if sort_order == 'desc' else 'desc'

    if episode_guid:
        published_at = (db.session.query(EpisodeNew.published_at)
                        .filter(EpisodeNew.guid == episode_guid)
                        .scalar())

    columns = [
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
    stmt = (db.session.query(*columns)
            .join(Podcast, EpisodeNew.podcast_id == Podcast.id)
            .filter(Podcast.guid == podcast_guid)
            .filter(EpisodeNew.status == EpisodeStatus.ACTIVE)
            .filter(EpisodeNew.published_at != None))

    query_sort_order = sort_order
    if episode_guid and published_at:
        if not start_after:
            query_sort_order = reverse_order
        compare = operator.lt if query_sort_order == 'desc' else operator.gt
        stmt = stmt.filter(compare((EpisodeNew.published_at, EpisodeNew.guid),
                           (published_at, episode_guid)))

    stmt = (stmt.order_by(getattr(EpisodeNew.published_at, query_sort_order)(),
                          getattr(EpisodeNew.guid, query_sort_order)())
            .limit(page_size))

    episodes = stmt.all()
    schema = EpisodeSchema(many=True)
    results = schema.dump(episodes)
    has_more = len(results) == page_size
    if has_more:
        del results[-1]

    if query_sort_order != sort_order and isinstance(results, list):
        results.reverse()

    return {
        'results': results,
        'count': len(results),
        'hasMore': has_more
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
