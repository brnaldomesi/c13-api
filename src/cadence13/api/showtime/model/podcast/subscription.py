from datetime import datetime, timezone
from sqlalchemy import and_
from cadence13.db.tables import PodcastSubscription, PodcastSubscriptionType


def get_subscription(session, podcast_id, field_name):
    return (session.query(PodcastSubscription)
            .join(PodcastSubscriptionType)
            .filter(PodcastSubscription.podcast_id == podcast_id)
            .filter(PodcastSubscriptionType.field_name == field_name)
            .one_or_none())


def get_subscription_urls(session, podcast_id):
    stmt = (session.query(
                PodcastSubscriptionType.field_name,
                PodcastSubscription.subscription_url,
                PodcastSubscription.disable_sync,
                PodcastSubscription.deleted
            )
            .outerjoin(PodcastSubscription, and_(
                PodcastSubscription.subscription_type_id == PodcastSubscriptionType.id,
                PodcastSubscription.podcast_id == podcast_id
            ))
            .filter(PodcastSubscriptionType.is_active == True))
    return stmt.all()


def create_subscription(session, podcast_id, field_name, params):
    subquery = (session.query(PodcastSubscriptionType.id)
                .filter_by(field_name=field_name))
    row = PodcastSubscription(
        podcast_id=podcast_id,
        subscription_type_id=subquery,
        subscription_url=params['subscription_url'] if params.get('subscription_url') else None,
        deleted=not params.get('subscription_url') or params.get('deleted', False),
        disable_sync=params.get('disable_sync', False)
    )
    session.add(row)
    session.commit()


def get_locked_sync_fields(session, podcast_id):
    stmt = (session.query(PodcastSubscriptionType.field_name)
            .join(PodcastSubscription, PodcastSubscription.subscription_type_id == PodcastSubscriptionType.id)
            .filter(PodcastSubscription.podcast_id == podcast_id)
            .filter(PodcastSubscription.disable_sync == True))
    rows = stmt.all()
    return [r[0] for r in rows]


def update_locked_sync_fields(session, podcast_id, locked_fields):
    existing = set(get_locked_sync_fields(session, podcast_id))
    desired = set(locked_fields)
    unlock = existing - desired
    lock = desired - existing
    new = []

    for field in unlock:
        row = get_subscription(session, podcast_id, field)
        if row:
            row.disable_sync = False
        else:
            new.append((field, False))

    for field in lock:
        row = get_subscription(session, podcast_id, field)
        if row:
            row.disable_sync = True
        else:
            new.append((field, True))

    # Commit the updated fields
    try:
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

    # Create new fields
    for field, disable_sync in new:
        create_subscription(session, podcast_id, field, {'disable_sync': disable_sync})


def update_subscription(session, podcast_id, params):
    field_name = params.pop('field_name')
    row = get_subscription(session, podcast_id, field_name)
    if not row:
        return create_subscription(session, podcast_id, field_name, params)
    if 'subscription_url' in params:
        params['deleted'] = not params['subscription_url']
    params['updated_at'] = datetime.now(timezone.utc)
    for k, v in params.items():
        setattr(row, k, v)
    session.commit()
