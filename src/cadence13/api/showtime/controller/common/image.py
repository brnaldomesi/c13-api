import json
from base64 import urlsafe_b64encode
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

import boto3
import os.path
from time import time

from cadence13.api.util.config import config_manager
from cadence13.api.util.db import db
from cadence13.db.tables import S3Image

PRESIGNED_POST_EXPIRATION = 600


def create_presigned_post(file_name: str, content_type: str, prefix: str):
    base_name, file_extension = os.path.splitext(file_name)
    key = f'{prefix.rstrip("/")}/{int(time())}{file_extension}'

    config = config_manager.get_config()
    bucket = config['showtime']['images']['bucket']

    s3 = boto3.client('s3')
    response = s3.generate_presigned_post(
        Bucket=bucket,
        Key=key,
        Fields={
            'Content-Type': content_type
        },
        Conditions=[
            {'bucket': bucket},
            {'key': key},
            {'Content-Type': content_type}
        ],
        ExpiresIn=PRESIGNED_POST_EXPIRATION
    )

    db.session.add(S3Image(
        bucket=bucket,
        key=key
    ))
    db.session.commit()

    return {
        'location': f'{response["url"]}{response["fields"]["key"]}',
        'formData': response
    }


def generate_resized_url(url, size=0):
    parsed = urlparse(url)
    if parsed.netloc.endswith('s3.amazonaws.com'):
        return generate_s3_resized_url(url, size)
    if parsed.netloc.endswith('imgix.net'):
        return generate_imgix_resized_url(url, size)


def generate_s3_resized_url(url, size):
    parsed = urlparse(url)
    if not parsed.netloc.endswith('s3.amazonaws.com'):
        return
    config = config_manager.get_config()
    image_handler_base_url = config['showtime']['images']['image_handler_base_url']
    payload = {
        'bucket': parsed.netloc.split('.')[0],
        'key': parsed.path.lstrip('/')
    }
    if size:
        payload['edits'] = {
            'resize': {
                'width': size,
                'height': size,
                'fit': 'inside'
            }
        }
    path = str(urlsafe_b64encode(json.dumps(payload).encode('utf-8')), 'utf-8')
    return f'{image_handler_base_url}/{path}'


def generate_imgix_resized_url(url, size=0):
    if not size:
        return url
    parsed_url = urlparse(url)
    if not parsed_url.netloc.endswith('imgix.net'):
        return

    # Parse the query string, add the new size parameters, and
    # rebuild a new query string
    parsed_qs = parse_qsl(parsed_url.query)
    parsed_qs.extend([
        ('width', str(size)),
        ('height', str(size))
    ])
    new_qs = urlencode(parsed_qs)

    # The named tuple isn't mutable, but a list is
    parsed_url = list(parsed_url)
    parsed_url[4] = new_qs

    return urlunparse(parsed_url)
