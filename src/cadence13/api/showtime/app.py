from cadence13.api.util.logging import get_logger
import os.path
import connexion
from cadence13.api.util.db import db
from cadence13.api.util.config import config_manager

logger = get_logger(__name__)
logger.info('Setting up application')

# Create the Connexion application instance
rest_app = connexion.FlaskApp(__name__, specification_dir='../openapi')

# Read the swagger.yml file to configure the endpoints
rest_app.add_api('showtime.yaml', validate_responses=True)

# Load config file
config_url = os.environ.get('CONFIG_URL')
config_manager.load_url(config_url)
config = config_manager.get_config()

# Get the underlying Flask application
app = rest_app.app

# Configure the app with database settings
app.config['SQLALCHEMY_DATABASE_URI'] = config['database_url']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    rest_app.run(host='0.0.0.0', port=5000, debug=True)
