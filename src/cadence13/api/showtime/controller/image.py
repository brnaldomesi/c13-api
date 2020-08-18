import os.path
from uuid import uuid4
import boto3
from flask_jwt_extended import jwt_required

from cadence13.api.util.config import config_manager
from cadence13.api.util.db import db
# from cadence13.db.enums.values import S3ImageType
from cadence13.db.tables import S3Image

PRESIGNED_POST_EXPIRATION = 600


@jwt_required
def create_presigned_post(body: dict) -> None:
    file_name = body['fileName']
    base_name, file_extension = os.path.splitext(file_name)

    # image_type = S3ImageType[body['imageType']]
    # TODO: handle errors if image type is invalid

    image_id = str(uuid4())
    key = f'{image_id}{file_extension}'
    # TODO: insert this into DB

    config = config_manager.get_config()
    bucket = config['showtime']['images']['bucket']

    s3 = boto3.client('s3')
    response = s3.generate_presigned_post(
        Bucket=bucket,
        Key=key,
        Fields={'Content-Type': body['contentType']},
        Conditions=[
            ['starts-with', '$Content-Type', 'image/']
        ],
        ExpiresIn=PRESIGNED_POST_EXPIRATION
    )

    db.session.add(S3Image(
        id=image_id,
        # type=image_type,
        bucket=bucket,
        key=key
    ))
    db.session.commit()

    return response
