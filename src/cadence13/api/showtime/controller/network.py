from flask_jwt_extended import jwt_required
from sqlalchemy.sql.functions import count
from marshmallow import fields, Schema, post_dump, pre_dump
from cadence13.db.tables import Network, Podcast, PodcastConfig
from cadence13.api.util.db import db
from cadence13.api.showtime.schema.db import NetworkSchema
from cadence13.api.showtime.schema.api import ApiPodcastSchema
from cadence13.api.showtime.db.table import ApiPodcast
from cadence13.db.enums.values import PodcastStatus, NetworkStatus
from cadence13.api.util.logging import get_logger
from cadence13.api.showtime.controller.podcast import update_podcast
from uuid import UUID, uuid4
from sqlalchemy.sql.functions import now
import connexion
from http import HTTPStatus

logger = get_logger(__name__)


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
    total = (db.session.query(Network.id).count())
    rows = (db.session.query(Network, count(ApiPodcast.id).label('podcast_count'))
            .outerjoin(ApiPodcast, Network.id == ApiPodcast.network_id)
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
           .filter(Network.id == networkId)
           .one_or_none())

    if not row:
        return 'Not found', 404

    schema = NetworkSchema()
    result = schema.dump(row)
    return result


@jwt_required
def create_network(body):
    networkId = uuid4()
    schema = NetworkSchema()
    deserialized = schema.load(body)
    logger.info(deserialized)

    row = Network(
        id=str(networkId),
        created_on=now(),
        **deserialized,
    )
    db.session.add(row)
    db.session.commit()
    schema = NetworkSchema()
    result = schema.dump(row)
    return result


def _disable_network_podcasts(network_id, delete=False):
    rows = (db.session.query(Podcast, PodcastConfig)
            .join(PodcastConfig, PodcastConfig.id == Podcast.podcast_config_id)
            .filter(Podcast.network_id == network_id)
            .all())
    if rows is not None:
        for podcast, config in rows:
            config.enable_show_page = False
            config.enable_show_hub = False
            config.enable_player = False
            if delete:
                podcast.network_id = None


@jwt_required
def update_network(networkId, body: dict):
    network_id = networkId
    schema = NetworkSchema()
    deserialized = schema.load(body)

    network = (db.session.query(Network)
               .filter_by(id=networkId)
               .one_or_none())
    if not network:
        return connexion.problem(
            HTTPStatus.NOT_FOUND,
            HTTPStatus.NOT_FOUND.phrase,
            f'Network {network_id} not found'
        )

    status_changed = False
    if 'status' in deserialized:
        status_changed = network.status != deserialized['status']

    for k, v in deserialized.items():
        if hasattr(network, k):
            setattr(network, k, v)

    if status_changed and network.status is not NetworkStatus.ACTIVE:
        _disable_network_podcasts(network_id, delete=False)

    db.session.commit()
    return get_network(networkId)


@jwt_required
def delete_network(networkId):
    network_id = networkId
    network = (db.session.query(Network)
               .filter_by(id=networkId)
               .one_or_none())
    if not network:
        return connexion.problem(
            HTTPStatus.NOT_FOUND,
            HTTPStatus.NOT_FOUND.phrase,
            f'Network {network_id} not found'
        )
    network.status = NetworkStatus.INACTIVE
    _disable_network_podcasts(network_id, delete=True)
    db.session.commit()


@jwt_required
def get_podcasts(networkId):
    podcasts = (db.session.query(ApiPodcast)
                .filter(ApiPodcast.network_id == networkId)
                .all())
    schema = ApiPodcastSchema(many=True)
    result = schema.dump(podcasts)
    return result
