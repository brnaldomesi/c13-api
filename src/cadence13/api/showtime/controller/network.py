from flask_jwt_extended import jwt_required
from sqlalchemy.sql.functions import count
from marshmallow import fields, Schema, post_dump, pre_dump
from cadence13.db.tables import Network
from cadence13.api.util.db import db
from cadence13.api.common.schema.db import NetworkSchema
from cadence13.api.common.schema.api import ApiPodcastSchema
from cadence13.api.common.db.table import ApiPodcast
from cadence13.db.enums import PodcastStatus, NetworkStatus


# Not sure if this should go into common.schema
# since this might be the only place this is used.
class ApiNetworkListSchema(Schema):
    network = fields.Nested(NetworkSchema, data_key='Network')
    podcast_count = fields.Integer(data_key='podcastCount')

    @pre_dump(pass_many=False)
    def pre_dump(self, data, many, **kwargs):
        return {
            'network': data[0],
            'podcast_count': data[1]
        }

    @post_dump(pass_many=False)
    def post_dump(self, data, many, **kwargs):
        data['Network']['podcastCount'] = data['podcastCount']
        return data['Network']


@jwt_required
def get_networks():
    total = (db.session.query(Network.id)
             .filter_by(status=NetworkStatus.ACTIVE.name).count())
    # FIXME: The network table is old and stores the status as a string
    # and not enum. Eventually that should change.
    rows = (db.session.query(Network, count(ApiPodcast.id).label('podcast_count'))
            .join(ApiPodcast, Network.id == ApiPodcast.network_id)
            .filter(ApiPodcast.status == PodcastStatus.ACTIVE)
            .filter(Network.status == NetworkStatus.ACTIVE.name)
            .group_by(Network).all())
    schema = ApiNetworkListSchema(many=True)
    data = schema.dump(rows)
    return {
        'total': total,
        'data': data
    }


@jwt_required
def get_network(networkId):
    row = (db.session.query(Network)
            .filter_by(status='ACTIVE')
            .filter(Network.id == networkId)
            .one_or_none())

    if not row:
        return 'Not found', 404

    schema = NetworkSchema()
    result = schema.dump(row)
    return result


@jwt_required
def create_network():
    return 'Not implemented', 501


@jwt_required
def get_podcasts(networkId):
    podcasts = (db.session.query(ApiPodcast)
                .filter(ApiPodcast.status == PodcastStatus.ACTIVE)
                .filter(ApiPodcast.network_id == networkId)
                .all())
    schema = ApiPodcastSchema(many=True)
    result = schema.dump(podcasts)
    return result
