import os
import click
from sqlalchemy import create_engine
from sqlalchemy.pool import SingletonThreadPool
from sqlalchemy.orm import sessionmaker
from cadence13.api.showtime.model.user import create_user
from cadence13.api.util.config import config_manager

Session = sessionmaker()


def get_password():
    password = click.prompt('Password', type=str, hide_input=True)
    password_confirm = click.prompt('Verify Password', type=str, hide_input=True)
    if password != password_confirm:
        click.echo('Passwords do not match! Try again.')
    return password


@click.command()
@click.option('--first-name', type=str)
@click.option('--last-name', type=str)
@click.option('--email', type=str)
@click.option('--password', type=str)
@click.option('--autoconfirm/--no-autoconfirm', default=False)
def main(first_name, last_name, email, password, autoconfirm):
    config_url = os.environ.get('CONFIG_URL')
    config_manager.load_url(config_url)
    config = config_manager.get_config()

    engine = create_engine(config['database_url'], poolclass=SingletonThreadPool)
    Session.configure(bind=engine)
    session = Session()
    if not first_name:
        first_name = click.prompt('First Name', type=str)
    if not last_name:
        last_name = click.prompt('Last Name', type=str)
    if not email:
        email = click.prompt('Email', type=str)
    while not password:
        password = get_password()

    click.echo()
    click.echo(f'First Name: {first_name}')
    click.echo(f'Last Name: {last_name}')
    click.echo(f'Email: {email}')

    if not autoconfirm:
        click.confirm('Create user?', abort=True)

    create_user(session, first_name, last_name, email, password)
    click.echo('Done!')


if __name__ == '__main__':
    main()
