from cadence13.api.util.logging import get_logger
import os.path
import connexion
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from cadence13.api.util.db import db
from cadence13.api.util.config import config_manager
from cadence13.api.util.routing import PrefixResolver

logger = get_logger(__name__)
logger.info('Setting up application')

# Create the Connexion application instance
rest_app = connexion.FlaskApp(__name__, specification_dir='../openapi')

# Read the swagger.yml file to configure the endpoints
rest_app.add_api('showtime.yaml',
                 validate_responses=True,
                 resolver=PrefixResolver('cadence13.api.showtime.controller.'))

# Load config file
config_url = os.environ.get('CONFIG_URL')
config_manager.load_url(config_url)
config = config_manager.get_config()

# Get the underlying Flask application
app = rest_app.app

# Configure CORS
origins = [
    'localhost',
    'https://showtime.cadence13.com',
    'https://showtime-test.cadence13.io',
    'https://showtime-dev.cadence13.io'
]
CORS(app, origins=origins, supports_credentials=True, max_age=3600)

# Configure the app with database settings
app.config['SQLALCHEMY_DATABASE_URI'] = config['database_url']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Configure JWT
# Configure application to store JWTs in cookies
app.config['JWT_TOKEN_LOCATION'] = ['cookies']

# Only allow JWT cookies to be sent over https. In production, this
# should likely be True
app.config['JWT_COOKIE_SECURE'] = os.environ.get('ENV', '').lower() in ('prod', 'test')

# Set the cookie paths, so that you are only sending your access token
# cookie to the access endpoints, and only sending your refresh token
# to the refresh endpoint. Technically this is optional, but it is in
# your best interest to not send additional cookies in the request if
# they aren't needed.
# app.config['JWT_ACCESS_COOKIE_PATH'] = '/api/'
app.config['JWT_REFRESH_COOKIE_PATH'] = '/token/refresh'

# Enable csrf double submit protection. See this for a thorough
# explanation: http://www.redotheweb.com/2015/11/09/api-security.html
app.config['JWT_COOKIE_CSRF_PROTECT'] = True

# Set the secret key to sign the JWTs with
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this!
app.config['JWT_CSRF_IN_COOKIES'] = False

jwt = JWTManager(app)


# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    rest_app.run(host='0.0.0.0', port=5000, debug=True)
