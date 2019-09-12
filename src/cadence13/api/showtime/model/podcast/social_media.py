from datetime import datetime, timezone
from sqlalchemy import and_
from cadence13.db.tables import PodcastSocialMedia, PodcastSubscriptionType


def get_social_media(session, podcast_id, field_name):
    return (session.query(PodcastSocialMedia)
            .join(PodcastSubscriptionType)
            .filter(PodcastSocialMedia.podcast_id == podcast_id)
            .filter(PodcastSubscriptionType.field_name == field_name)
            .one_or_none())


def get_social_media_urls(session, podcast_id):
    stmt = (session.query(
                PodcastSubscriptionType.field_name,
                PodcastSocialMedia.social_media_url,
                PodcastSocialMedia.disable_sync,
                PodcastSocialMedia.deleted
            )
            .outerjoin(PodcastSocialMedia, and_(
                PodcastSocialMedia.social_media_type_id == PodcastSubscriptionType.id,
                PodcastSocialMedia.podcast_id == podcast_id
            ))
            .filter(PodcastSubscriptionType.is_active == True))
    return stmt.all()


def create_social_media(session, podcast_id, field_name, params):
    subquery = (session.query(PodcastSubscriptionType.id)
                .filter_by(field_name=field_name))
    row = PodcastSocialMedia(
        podcast_id=podcast_id,
        social_media_type_id=subquery,
        social_media_url=params['social_media_url'] if params.get('social_media_url') else None,
        deleted=not params.get('social_media_url') or params.get('deleted', False),
        disable_sync=params.get('disable_sync', False)
    )
    session.add(row)
    session.commit()


def get_locked_sync_fields(session, podcast_id):
    stmt = (session.query(PodcastSubscriptionType.field_name)
            .join(PodcastSocialMedia, PodcastSocialMedia.social_media_type_id == PodcastSubscriptionType.id)
            .filter(PodcastSocialMedia.podcast_id == podcast_id)
            .filter(PodcastSocialMedia.disable_sync == True))
    rows = stmt.all()
    return [r[0] for r in rows]


def update_locked_sync_fields(session, podcast_id, locked_fields):
    existing = set(get_locked_sync_fields(session, podcast_id))
    desired = set(locked_fields)
    unlock = existing - desired
    lock = desired - existing

    for field in unlock:
        row = get_social_media(session, podcast_id, field)
        if row:
            row.disable_sync = False
        else:
            create_social_media(session, podcast_id, field, {'disable_sync': False})

    for field in lock:
        row = get_social_media(session, podcast_id, field)
        if row:
            row.disable_sync = True
        else:
            create_social_media(session, podcast_id, field, {'disable_sync': True})


def update_social_media(session, podcast_id, params):
    field_name = params.pop('field_name')
    row = get_social_media(session, podcast_id, field_name)
    if not row:
        return create_social_media(session, podcast_id, field_name, params)
    if 'social_media_url' in params:
        params['deleted'] = not params['social_media_url']
    params['updated_at'] = datetime.now(timezone.utc)
    for k, v in params.items():
        setattr(row, k, v)
    session.commit()
