from http import HTTPStatus

import connexion
from flask_jwt_extended import jwt_required
from marshmallow import Schema, fields, pre_load, post_dump

import cadence13.api.showtime.controller.common.image as common_image
from cadence13.api.showtime.controller.common.image import generate_image_result
from cadence13.api.util.db import db
from cadence13.db.tables import ShowHubConfig

IMAGE_TYPE_PREFIX_MAP = {
    'logo': 'show-hub/logo',
    'bgDesktop': 'show-hub/background/desktop',
    'bgTabletLandscape': 'show-hub/background/tablet/landscape',
    'bgTabletPortrait': 'show-hub/background/tablet/portrait',
    'bgMobilePortrait': 'show-hub/background/mobile/portrait'
}


class ShowHubConfigSchema(Schema):
    headline = fields.String()
    sub_headline = fields.String(data_key='subHeadline')
    logo_url = fields.String(data_key='logoUrl')
    bg_desktop_url = fields.String(data_key='bgDesktopUrl')
    bg_tablet_landscape_url = fields.String(data_key='bgTabletLandscapeUrl')
    bg_tablet_portrait_url = fields.String(data_key='bgTabletPortraitUrl')
    bg_mobile_portrait_url = fields.String(data_key='bgMobilePortraitUrl')

    @pre_load(pass_many=False)
    def pre_load(self, data, many, **kwargs):
        if 'images' not in data:
            return data  # nothing to be done

        for k, v in data['images'].items():
            data[f'{k}Url'] = v['sourceUrl']
        del data['images']
        return data

    @post_dump(pass_many=False)
    def post_dump(self, data, many, **kwargs):
        data['images'] = generate_image_result({
            k: data[f'{k}Url'] for k in IMAGE_TYPE_PREFIX_MAP.keys()
        }, sizes=[])
        for k in IMAGE_TYPE_PREFIX_MAP.keys():
            del data[f'{k}Url']
        return data


@jwt_required
def get_config():
    row = db.session.query(ShowHubConfig).first()
    if not row:
        return connexion.problem(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
            'Show Hub config not found')
    schema = ShowHubConfigSchema()
    return schema.dump(row)


@jwt_required
def update_config(body):
    schema = ShowHubConfigSchema()
    deserialized = schema.load(body)
    config = db.session.query(ShowHubConfig).first()
    if not config:
        return connexion.problem(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
            'Show Hub config not found')
    for k, v in deserialized.items():
        if hasattr(config, k):
            setattr(config, k, v)
    db.session.commit()


@jwt_required
def create_presigned_post(body):
    image_type = body['imageType']
    try:
        prefix = IMAGE_TYPE_PREFIX_MAP[image_type]
    except KeyError:
        return connexion.problem(
            HTTPStatus.NOT_FOUND,
            HTTPStatus.NOT_FOUND.phrase,
            f'Image type "{image_type}" not found')
    return common_image.create_presigned_post(
        file_name=body['fileName'],
        content_type=body['contentType'],
        prefix=prefix
    )
