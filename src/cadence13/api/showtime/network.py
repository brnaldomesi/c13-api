from marshmallow import Schema, fields
from cadence13.db.tables import Network, Podcast, NetworkSeriesMap
from cadence13.db.enums import PodcastStatus
from cadence13.api.util.db import db
from cadence13.api.util.string import underscore_to_camelcase
from cadence13.api.common.schema.db import PodcastSchema


class NetworkSchema(Schema):
    #fixme: make network IDs all UUIDs
    guid = fields.String(attribute='network_id')
    name = fields.String()


def get_networks():
    networks = (db.session.query(Network)
                .filter_by(status='ACTIVE').all())
    schema = NetworkSchema(many=True)
    result = schema.dump(networks)
    return result


def create_network():
    return 'Not implemented', 501


def get_podcasts(networkGuid):
    podcasts = (db.session.query(Podcast)
                .join(NetworkSeriesMap, NetworkSeriesMap.series_id == Podcast.series_id)
                .filter(Podcast.status == PodcastStatus.ACTIVE)
                .filter(NetworkSeriesMap.network_id == networkGuid)
                .all())
    schema = PodcastSchema(many=True)
    result = schema.dump(podcasts)
    return result

