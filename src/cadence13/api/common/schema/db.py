from marshmallow import Schema, fields
from marshmallow_enum import EnumField
import cadence13.db.enums as db_enums


class NetworkSchema(Schema):
    id = fields.UUID()
    name = fields.String()
    cover_img_url = fields.String()


class PodcastSchema(Schema):
    guid = fields.UUID()
    slug = fields.String()
    title = fields.String()
    subtitle = fields.String()
    summary = fields.String()
    podcast_type = EnumField(db_enums.PodcastType, data_key='podcastType')
    copyright = fields.String()
    author = fields.String()
    website_url = fields.Url(data_key='websiteUrl')
    image_url = fields.Url(data_key='imageUrl')
    owner_name = fields.String(data_key='ownerName')
    owner_email = fields.Email(data_key='ownerEmail')
    is_explicit = fields.Boolean(data_key='isExplicit')
    is_complete = fields.Boolean(data_key='isComplete')
    tags = fields.List(fields.String())
    status = EnumField(db_enums.PodcastStatus)
    created_at = fields.DateTime(data_key='createdAt')
    updated_at = fields.DateTime(data_key='updatedAt')
    network_id = fields.UUID(data_key='networkId')


class PodcastConfigSchema(Schema):
    locked_sync_fields = fields.List(fields.String(), data_key='lockedSyncFields')


class PodcastCategorySchema(Schema):
    id = fields.UUID()
    hash = fields.String()
    name = fields.String()


class EpisodeSchema(Schema):
    guid = fields.UUID()
    podcast_guid = fields.UUID(data_key='podcastGuid')
    season_no = fields.Integer(data_key='seasonNo')
    episode_no = fields.Integer(data_key='episodeNo')
    title = fields.String()
    subtitle = fields.String()
    summary = fields.String()
    author = fields.String()
    episode_type = EnumField(db_enums.EpisodeType, data_key='episodeType')
    image_url = fields.Url(data_key='imageUrl')
    audio_url = fields.Url(data_key='audioUrl')
    is_explicit = fields.Boolean(data_key='isExplicit')
    published_at = fields.DateTime(data_key='publishedAt')
    status = EnumField(db_enums.EpisodeStatus)
    created_at = fields.DateTime(data_key='createdAt')
    updated_at = fields.DateTime(data_key='updatedAt')