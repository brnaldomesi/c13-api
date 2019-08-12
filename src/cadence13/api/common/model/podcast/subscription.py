from cadence13.api.util.logging import get_logger
from datetime import datetime, timezone
from cadence13.db.tables import PodcastSubscriptionMap, SubscriptionService

logger = get_logger(__name__)


def get_subscription(session, podcast_id, field_name):
    return (session.query(PodcastSubscriptionMap)
            .join(SubscriptionService)
            .filter(PodcastSubscriptionMap.podcast_id == podcast_id)
            .filter(SubscriptionService.field_name == field_name)
            .one_or_none())


def create_subscription(session, podcast_id, field_name, params):
    subquery = (session.query(SubscriptionService.id)
                .filter_by(field_name=field_name))
    row = PodcastSubscriptionMap(
        podcast_id=podcast_id,
        subscription_service_id=subquery,
        subscription_url=params['subscription_url'] if params.get('subscription_url') else None,
        deleted=not params.get('subscription_url') or params.get('deleted', False),
        disable_sync=params.get('disable_sync', False)
    )
    session.add(row)
    session.commit()


def get_locked_sync_fields(session, podcast_id):
    stmt = (session.query(SubscriptionService.field_name)
            .join(PodcastSubscriptionMap, PodcastSubscriptionMap.subscription_service_id == SubscriptionService.id)
            .filter(PodcastSubscriptionMap.podcast_id == podcast_id)
            .filter(PodcastSubscriptionMap.disable_sync == True))
    rows = stmt.all()
    return [r[0] for r in rows]


def update_locked_sync_fields(session, podcast_id, locked_fields):
    existing = set(get_locked_sync_fields(session, podcast_id))
    logger.info('existing: {}'.format(existing))
    desired = set(locked_fields)
    unlock = existing - desired
    logger.info('to unlock: {}'.format(unlock))
    lock = desired - existing
    logger.info('to lock: {}'.format(lock))

    for field in unlock:
        row = get_subscription(session, podcast_id, field)
        if row:
            row.disable_sync = False
        else:
            create_subscription(session, podcast_id, field, {'disable_sync': False})

    for field in lock:
        row = get_subscription(session, podcast_id, field)
        if row:
            row.disable_sync = True
        else:
            create_subscription(session, podcast_id, field, {'disable_sync': True})


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
