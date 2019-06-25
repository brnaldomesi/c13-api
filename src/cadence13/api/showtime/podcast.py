from cadence13.api.util.logging import get_logger
import cadence13.api.common.podcast as common_podcast
import time
import boto3

logger = get_logger(__name__)


def get_podcasts(startAfter=None, endingBefore=None,
                 limit=common_podcast.PODCASTS_LIMIT):
    return common_podcast.get_podcasts(
        startAfter, endingBefore, limit)


def get_podcast(podcastGuid):
    return common_podcast.get_podcast(podcastGuid)


def update_podcast(podcastGuid, body: dict):
    return common_podcast.update_podcast(podcastGuid, body)


def get_episodes(podcastGuid, startAfter=None, endingBefore=None,
                 limit=common_podcast.EPISODES_LIMIT,
                 sortOrder='desc'):
    return common_podcast.get_episodes(
        podcast_guid=podcastGuid,
        start_after=startAfter,
        ending_before=endingBefore,
        limit=limit,
        sort_order=sortOrder
    )


def assign_network():
    return 'Not implemented', 501


def get_subscription_urls(podcastGuid):
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


def patch_subscription_urls(podcastGuid, body):
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


def get_social_media_urls(podcastGuid):
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


def patch_social_media_urls(podcastGuid, body):
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


def get_crew_members(podcastGuid):
    return [
        {
            'guid': 'd858bc53-9c3b-4bb8-a163-c58df7800121',
            'podcastGuid': podcastGuid,
            'firstName': 'Jon',
            'middleName': None,
            'lastName': 'Favreau',
            'imageUrls':  {
                'original': 'https://content.production.cdn.art19.com/images/bf/fa/50/92/bffa5092-df8d-41d6-9ea1-02b70693f41d/3183fa58305f036c4a18fb6c86f18475eccb419143f43f005dc79c01d9dd77f07441389356575e508606d89fc47e4d8a9f058514380f5f8fe97e653b7daa7c96.jpeg'
            }
        },
        {
            'guid': '4ca17120-86d4-4474-bd5e-3e5d4d521947',
            'podcastGuid': podcastGuid,
            'firstName': 'Jon',
            'middleName': None,
            'lastName': 'Lovett',
            'imageUrls': {
                'original': 'https://content.production.cdn.art19.com/images/9a/9d/b0/8d/9a9db08d-843c-4b5d-b910-ffa9ed5d9a45/dd651d867f85fc4fd6f3230d662df6cb2dd9858c7a5e973a40129cabb6f5e61022c7ea9f887d2bbfdbc4de8081d3c93d328ca9ae320b9a0d9e0eb2d95948f243.jpeg'
            }
        },
        {
            'guid': '6f93d51f-ac2a-4159-9430-1337e0324425',
            'podcastGuid': podcastGuid,
            'firstName': 'Dan',
            'middleName': None,
            'lastName': 'Pfeiffer',
            'imageUrls': {}
        }
    ]


def create_image_upload_url(podcastGuid):
    # s3 = boto3.client('s3',
    #   aws_access_key_id='',
    #   aws_secret_access_key=''
    # )
    s3 = boto3.client('s3')
    key = 'podcasts/{}/{}/original.jpg'.format(podcastGuid, int(time.time()))
    return s3.generate_presigned_post(
        Bucket='cadence13-showtime-upload-test',
        Key=key,
        Conditions=[
            {'acl': 'public-read'},
            {'Content-Type': 'image/jpeg'}
        ],
        ExpiresIn=600
    )
