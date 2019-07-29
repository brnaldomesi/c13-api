import os
from sqlalchemy import create_engine
from sqlalchemy.pool import SingletonThreadPool
from sqlalchemy.orm import sessionmaker
from cadence13.api.showtime.model.user import create_user
from cadence13.api.util.config import config_manager

Session = sessionmaker()


def main():
    config_url = os.environ.get('CONFIG_URL')
    config_manager.load_url(config_url)
    config = config_manager.get_config()

    engine = create_engine(config['database_url'], poolclass=SingletonThreadPool)
    Session.configure(bind=engine)
    session = Session()
    create_user(session)


if __name__ == '__main__':
    main()
