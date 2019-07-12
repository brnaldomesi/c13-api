from marshmallow import Schema, fields, pre_load, pre_dump, post_dump
from cadence13.api.common.schema.db import PodcastSchema, PodcastConfigSchema, EpisodeSchema


class ApiPodcastSchema(Schema):
    podcast = fields.Nested(PodcastSchema(), attribute='Podcast')
    podcast_config = fields.Nested(PodcastConfigSchema(), attribute='PodcastConfig')

    @pre_load(pass_many=False)
    def split_to_db(self, data, many, **kwargs):
        podcast = data
        podcast_config = {}
        for key in ('lockedSyncFields',):
            if key not in podcast:
                continue
            podcast_config[key] = podcast[key]
            del podcast[key]
        return {
            'podcast': podcast,
            'podcast_config': podcast_config
        }

    @pre_dump(pass_many=False)
    def fill_missing_config(self, data, many, **kwargs):
        if not data.PodcastConfig:
            return {
                'Podcast': data.Podcast,
                'PodcastConfig': {
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


# Alias to the DB version of the schema since they're the same
ApiEpisodeSchema = EpisodeSchema