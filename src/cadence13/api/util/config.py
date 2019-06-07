import json
from urllib.parse import urlparse
import boto3


class ConfigManager:
    def __init__(self):
        self._config = None

    def load(self, file_obj):
        self._config = json.load(file_obj)

    def loads(self, config_str):
        self._config = json.loads(config_str)

    def load_url(self, config_url):
        result = urlparse(config_url)
        scheme = result.scheme if result.scheme else 'file'
        if scheme == 's3':
            s3 = boto3.client('s3')
            obj = s3.get_object(Bucket=result.netloc, Key=result.path.lstrip('/'))
            self.load(obj['Body'])
        elif scheme == 'file':
            with open(result.netloc + result.path, 'r') as fp:
                self.load(fp)
        else:
            raise Exception('Unsupported URL scheme: {}'.format(result.scheme))

    def get_config(self):
        if not self._config:
            raise SystemError('Not configured!')
        return self._config


config_manager = ConfigManager()
