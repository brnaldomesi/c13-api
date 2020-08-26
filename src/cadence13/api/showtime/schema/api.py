from cadence13.api.util.logging import get_logger
from marshmallow import Schema, fields, pre_load, post_dump
from cadence13.api.showtime.controller.common.image import generate_image_result
from .db import (
    PodcastSchema, PodcastConfigSchema, PodcastCategorySchema,
    EpisodeSchema, NetworkSchema)

logger = get_logger(__name__)

LOCKABLE_FIELDS_API_TO_DB = {
    'slug': 'SLUG',
    'title': 'TITLE',
    'subtitle': 'SUBTITLE',
    'summary': 'SUMMARY',
    'image': 'IMAGE',
    'websiteUrl': 'WEBSITE_URL'
}

LOCKABLE_FIELDS_DB_TO_API = {v: k for k, v in LOCKABLE_FIELDS_API_TO_DB.items()}


class ApiPodcastConfigSchema(PodcastConfigSchema):
    @pre_load(pass_many=False)
    def pre_load(self, data, many, **kwargs):
        if 'lockedSyncFields' in data:
            to_db_fields = [LOCKABLE_FIELDS_API_TO_DB[f] for f in data['lockedSyncFields']
                            if f in LOCKABLE_FIELDS_API_TO_DB]
            data['lockedSyncFields'] = to_db_fields
        return data

    @post_dump(pass_many=False)
    def post_dump(self, data, many, **kwargs):
        if 'lockedSyncFields' in data:
            to_api_fields = [LOCKABLE_FIELDS_DB_TO_API[f] for f in data['lockedSyncFields']
                             if f in LOCKABLE_FIELDS_DB_TO_API]
            data['lockedSyncFields'] = to_api_fields
        return data


class ApiPodcastSchema(PodcastSchema):
    config = fields.Nested(ApiPodcastConfigSchema)
    network = fields.Nested(NetworkSchema)
    categories = fields.Nested(PodcastCategorySchema, many=True)

    @post_dump(pass_many=False)
    def post_dump(self, data, many, **kwargs):
        # DEPRECATED: The image_url field is nested in imageUrls
        data['imageUrls'] = {'original': data['imageUrl']}
        del data['imageUrl']

        data['images'] = generate_image_result({
            'rssImage': data['rssImageUrl'],
            'cover': data['coverImageUrl'],
            'background': data['backgroundImageUrl']
        })
        del data['rssImageUrl']
        del data['coverImageUrl']
        del data['backgroundImageUrl']

        # Networks already get their own nested structure
        if 'networkId' in data:
            del data['networkId']
        return data


class PodcastSubscriptionSchema(Schema):
    field_name = fields.String()
    subscription_url = fields.Url(allow_none=True)
    disable_sync = fields.Boolean()


class PodcastSocialMediaSchema(Schema):
    field_name = fields.String()
    social_media_url = fields.Url()
    disable_sync = fields.Boolean()


# Alias to the DB version of the schema since they're the same
ApiEpisodeSchema = EpisodeSchema