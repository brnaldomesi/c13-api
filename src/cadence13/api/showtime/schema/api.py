from cadence13.api.util.logging import get_logger
from marshmallow import Schema, fields, pre_load, post_dump
from .db import (
    PodcastSchema, PodcastConfigSchema, PodcastCategorySchema,
    EpisodeSchema, NetworkSchema)

logger = get_logger(__name__)


class ApiPodcastSchema(PodcastSchema):
    config = fields.Nested(PodcastConfigSchema)
    network = fields.Nested(NetworkSchema)
    categories = fields.Nested(PodcastCategorySchema, many=True)

    @pre_load(pass_many=False)
    def split_to_db(self, data, many, **kwargs):
        if 'config' not in data:
            data['config'] = {}
        if 'lockedSyncFields' in data:
            data['config']['lockedSyncFields'] = data['lockedSyncFields']
            del data['lockedSyncFields']
        return data

    @post_dump(pass_many=False)
    def post_dump(self, data, many, **kwargs):
        # Special handling for config fields
        if data['config'] is not None:
            data['lockedSyncFields'] = data['config']['lockedSyncFields']
            del data['config']['lockedSyncFields']

        # The image_url field is nested in imageUrls
        data['imageUrls'] = {'original': data['imageUrl']}
        del data['imageUrl']

        # Networks already get their own nested structure
        if data.get('networkId'):
            del data['networkId']
        return data


class PodcastSubscriptionSchema(Schema):
    field_name = fields.String()
    subscription_url = fields.Url()
    disable_sync = fields.Boolean()


class PodcastSocialMediaSchema(Schema):
    field_name = fields.String()
    social_media_url = fields.Url()
    disable_sync = fields.Boolean()


# Alias to the DB version of the schema since they're the same
ApiEpisodeSchema = EpisodeSchema