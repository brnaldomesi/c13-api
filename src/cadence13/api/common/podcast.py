from cadence13.db.tables import Podcast, PodcastSocialMedia, PodcastSubscription
from cadence13.db.enums import PodcastStatus
from cadence13.api.util.db import db
from cadence13.api.util.string import underscore_to_camelcase
from cadence13.api.common.schema import PodcastSchema

PODCASTS_LIMIT = 25


def get_podcasts(start_after=None, ending_before=None, limit=PODCASTS_LIMIT):
    title = None
    podcast_guid = start_after or ending_before
    sort_order = 'asc'
    page_size = limit + 1

    if podcast_guid:
        title = (db.session.query(Podcast.title)
                 .filter(Podcast.guid == podcast_guid)
                 .scalar())

    stmt = (db.session.query(Podcast)
            .filter(Podcast.status == PodcastStatus.ACTIVE))
    if start_after and title:
        stmt = stmt.filter((Podcast.title, Podcast.guid) > (title, podcast_guid))
    elif ending_before and title:
        stmt = stmt.filter((Podcast.title, Podcast.guid) < (title, podcast_guid))
        sort_order = 'desc'
    stmt = (stmt.order_by(getattr(Podcast.title, sort_order)(),
                          getattr(Podcast.guid, sort_order)())
            .limit(page_size))

    podcasts = stmt.all()
    schema = PodcastSchema(many=True)
    results = schema.dump(podcasts)
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
    podcast = db.session.query(Podcast).filter_by(guid=podcast_guid).one_or_none()
    if not podcast:
        return 'Not found', 404

    schema = PodcastSchema()
    result = schema.dump(podcast)
    result['socialMedialUrls'] = get_social_media_urls(podcast.guid)
    result['subscriptionUrls'] = get_subscription_urls(podcast.guid)
    result['imageUrls'] = {'original': podcast.image_url}
    result['locked'] = []
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
