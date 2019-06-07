from marshmallow import Schema, fields
from marshmallow_enum import EnumField
import cadence13.db.enums as db_enums


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
    owner_name = fields.String(data_key='ownerName')
    owner_email = fields.Email(data_key='ownerEmail')
    is_explicit = fields.Boolean(data_key='isExplicit')
    is_complete = fields.Boolean(data_key='isComplete')
    status = EnumField(db_enums.PodcastStatus)
    created_at = fields.DateTime(data_key='createdAt')
    updated_at = fields.DateTime(data_key='updatedAt')