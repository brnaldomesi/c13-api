from cadence13.api.util.logging import get_logger
from marshmallow import Schema, fields, pre_load, pre_dump, post_dump
from cadence13.api.common.schema.db import (
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
        for key in ('lockedSyncFields',):
            if key not in data:
                continue
            data['config'][key] = data[key]
            del data[key]
        return data

    @post_dump(pass_many=False)
    def post_dump(self, data, many, **kwargs):
        data['id'] = data['guid']

        # Special handling for config fields
        config = data['config'] if data['config'] is not None else {}
        data['lockedSyncFields'] = config.get('lockedSyncFields', [])
        del data['config']

        # The image_url field is nested in imageUrls
        data['imageUrls'] = {'original': data['imageUrl']}
        del data['imageUrl']

        # Networks already get their own nested structure
        if data.get('networkId'):
            del data['networkId']
        return data


# Alias to the DB version of the schema since they're the same
ApiEpisodeSchema = EpisodeSchema