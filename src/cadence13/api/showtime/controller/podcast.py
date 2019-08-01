from cadence13.api.util.logging import get_logger
import time
import boto3
from flask_jwt_extended import jwt_required
from cadence13.api.util.db import db
from cadence13.db.tables import Podcast, PodcastConfig
import cadence13.api.common.controller.podcast as common_podcast
from cadence13.api.common.schema.db import PodcastConfigSchema
from cadence13.api.common.schema.api import ApiPodcastSchema

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

    if deserialized['config']:
        _update_podcast_config(podcastId, deserialized['config'])

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
    logger.info(podcast_guid)
    logger.info(params)

    row = (db.session.query(PodcastConfig)
           .join(Podcast, PodcastConfig.podcast_id == Podcast.id)
           .filter(Podcast.guid == podcast_guid)
           .one_or_none())

    if not row:
        logger.info('creating config for {}'.format(podcast_guid))
        return _create_podcast_config(podcast_guid, params)

    for k, v in params.items():
        if hasattr(row, k):
            logger.info('adding {} to update fields'.format(k))
            setattr(row, k, v)

    schema = PodcastConfigSchema()
    return schema.dump(row)


@jwt_required
def update_locked_sync_fields(podcastId, body):
    normalized = frozenset([field.lower() for field in body])
    podcast_config = _update_podcast_config(podcastId, {
        'locked_sync_fields': normalized
    })
    return podcast_config['locked_sync_fields']


@jwt_required
def update_podcast_tags(podcastId, body):
    normalized = frozenset([tag.lower() for tag in body])
    podcast_config = _update_podcast_config(podcastId, {
        'tags': normalized
    })
    return podcast_config['tags']


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
    return {
        'applePodcasts': 'https://itunes.apple.com/podcast/id1192761536',
        'googlePlay': None,
        'googlePodcasts': None,
        'stitcher': None,
        'spotify': 'https://open.spotify.com/show/5JGorGvdwljJHTl6wpMXN3',
        'radioCom': None,
        'iHeart': None,
        'locked': [
            'spotify'
        ]
    }


@jwt_required
def patch_subscription_urls(podcastId, body):
    response = {
        'applePodcasts': 'https://itunes.apple.com/podcast/id1192761536',
        'googlePlay': None,
        'googlePodcasts': None,
        'stitcher': None,
        'spotify': 'https://open.spotify.com/show/5JGorGvdwljJHTl6wpMXN3',
        'radioCom': None,
        'iHeart': None,
        'locked': [
            'spotify'
        ]
    }
    for k, v in body.items():
        if k in response:
            response[k] = v
    return response


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
    return [
        {
            'guid': 'd858bc53-9c3b-4bb8-a163-c58df7800121',
            'podcastId': podcastId,
            'firstName': 'Jon',
            'middleName': None,
            'lastName': 'Favreau',
            'imageUrls':  {
                'original': 'https://content.production.cdn.art19.com/images/bf/fa/50/92/bffa5092-df8d-41d6-9ea1-02b70693f41d/3183fa58305f036c4a18fb6c86f18475eccb419143f43f005dc79c01d9dd77f07441389356575e508606d89fc47e4d8a9f058514380f5f8fe97e653b7daa7c96.jpeg'
            }
        },
        {
            'guid': '4ca17120-86d4-4474-bd5e-3e5d4d521947',
            'podcastId': podcastId,
            'firstName': 'Jon',
            'middleName': None,
            'lastName': 'Lovett',
            'imageUrls': {
                'original': 'https://content.production.cdn.art19.com/images/9a/9d/b0/8d/9a9db08d-843c-4b5d-b910-ffa9ed5d9a45/dd651d867f85fc4fd6f3230d662df6cb2dd9858c7a5e973a40129cabb6f5e61022c7ea9f887d2bbfdbc4de8081d3c93d328ca9ae320b9a0d9e0eb2d95948f243.jpeg'
            }
        },
        {
            'guid': '6f93d51f-ac2a-4159-9430-1337e0324425',
            'podcastId': podcastId,
            'firstName': 'Dan',
            'middleName': None,
            'lastName': 'Pfeiffer',
            'imageUrls': {}
        }
    ]


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
