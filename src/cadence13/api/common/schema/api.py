from marshmallow import Schema, fields, pre_load, pre_dump, post_dump
from cadence13.api.common.schema.db import (
    PodcastSchema, PodcastConfigSchema, PodcastCategorySchema,
    EpisodeSchema, NetworkSchema)


class ApiPodcastSchema(PodcastSchema):
    config = fields.Nested(PodcastConfigSchema)
    network = fields.Nested(NetworkSchema)
    categories = fields.Nested(PodcastCategorySchema, many=True)

    @post_dump(pass_many=False)
    def merge_table(self, data, many, **kwargs):
        data['id'] = data['guid']
        data['lockedSyncFields'] = data.get('config', {}).get('lockedSyncFields', [])
        data['imageUrls'] = {'original': data['imageUrl']}
        del data['imageUrl']
        return data


# Alias to the DB version of the schema since they're the same
ApiEpisodeSchema = EpisodeSchema