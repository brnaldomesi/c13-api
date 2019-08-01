from flask_jwt_extended import jwt_required
from cadence13.db.tables import Network, Podcast, NetworkSeriesMap
from cadence13.db.enums import PodcastStatus
from cadence13.api.util.db import db
from cadence13.api.common.schema.db import PodcastSchema, NetworkSchema
from cadence13.api.common.schema.api import ApiPodcastSchema


@jwt_required
def get_networks():
    total = (db.session.query(Network.id)
             .filter_by(status='ACTIVE').count())
    networks = (db.session.query(Network)
                .filter_by(status='ACTIVE').all())
    schema = NetworkSchema(many=True)
    data = schema.dump(networks)
    return {
        'total': total,
        'data': data
    }


@jwt_required
def create_network():
    return 'Not implemented', 501


@jwt_required
def get_podcasts(networkId):
    podcasts = (db.session.query(Podcast)
                .join(NetworkSeriesMap, NetworkSeriesMap.series_id == Podcast.series_id)
                .filter(Podcast.status == PodcastStatus.ACTIVE)
                .filter(NetworkSeriesMap.network_id == networkId)
                .all())
    schema = PodcastSchema(many=True)
    result = schema.dump(podcasts)
    return result

