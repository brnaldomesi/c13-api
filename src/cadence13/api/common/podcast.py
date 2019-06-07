from cadence13.db.tables import Podcast, PodcastSocialMedia, PodcastSubscription
from cadence13.db.enums import PodcastStatus
from cadence13.api.util.db import db
from cadence13.api.util.string import underscore_to_camelcase
from cadence13.api.common.schema import PodcastSchema


def get_podcasts():
    podcasts = (db.session.query(Podcast)
                .filter_by(status=PodcastStatus.ACTIVE).all())
    schema = PodcastSchema(many=True)
    result = schema.dump(podcasts)
    return result


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
