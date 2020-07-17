from collections import OrderedDict
from functools import lru_cache
from uuid import uuid4
import re

from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.functions import now

import cadence13.db.enums.values as db_enums
from cadence13.api.util.db import db
from cadence13.api.util.logging import get_logger
from cadence13.db.tables import Category, CategoryPodcastMap, CategoryType, Podcast, PodcastConfig

logger = get_logger(__name__)


class InvalidCategoryType(Exception):
    pass


class CategoryNotFound(Exception):
    pass


class CategorySlugTaken(Exception):
    pass


@lru_cache()
def _get_category_type_id(key: str) -> str:
    return db.session.query(CategoryType.id).filter_by(key=key).scalar()


@jwt_required
def get_categories():
    rows = (db.session.query(Category, CategoryType.key)
            .join(CategoryType, Category.category_type_id == CategoryType.id)
            .filter(Category.deleted.is_(False),
                    CategoryType.is_active.is_(True))
            .order_by(Category.priority.desc())
            .all())
    categories = OrderedDict()
    for c, category_type in rows:
        categories[c.id] = {
            'id': c.id,
            'slug': c.slug,
            'priority': c.priority,
            'name': c.name,
            'type': category_type,
            'hidden': c.hidden,
            'podcasts': []
        }

    rows = (db.session.query(CategoryPodcastMap.category_id,
                             CategoryPodcastMap.podcast_id,
                             CategoryPodcastMap.priority,
                             Podcast.title,
                             Podcast.image_url)
            .join(Category, Category.id == CategoryPodcastMap.category_id)
            .join(Podcast, Podcast.id == CategoryPodcastMap.podcast_id)
            .join(PodcastConfig, PodcastConfig.id == Podcast.podcast_config_id)
            .filter(Category.deleted.is_(False),
                    Podcast.status == db_enums.PodcastStatus.ACTIVE,
                    PodcastConfig.enable_show_page.is_(True))
            .order_by(CategoryPodcastMap.priority.desc())
            .all())
    for r in rows:
        categories[r.category_id]['podcasts'].append({
            'id': r.podcast_id,
            'priority': r.priority,
            'title': r.title,
            'imageUrl': r.image_url
        })

    return list(categories.values())


@jwt_required
def get_category(categoryId):
    row = (db.session.query(Category, CategoryType.key)
           .join(CategoryType, Category.category_type_id == CategoryType.id)
           .filter(Category.id == categoryId,
                   Category.deleted.is_(False),
                   CategoryType.is_active.is_(True))
           .one_or_none())
    if not row:
        return 'Not found', 404

    category, category_type = row
    result = {
        'id': category.id,
        'slug': category.slug,
        'priority': category.priority,
        'name': category.name,
        'type': category_type,
        'hidden': category.hidden
    }

    rows = (db.session.query(CategoryPodcastMap.podcast_id,
                             CategoryPodcastMap.priority,
                             Podcast.title,
                             Podcast.image_url)
            .join(Podcast, Podcast.id == CategoryPodcastMap.podcast_id)
            .join(PodcastConfig, PodcastConfig.id == Podcast.podcast_config_id)
            .filter(CategoryPodcastMap.category_id == categoryId,
                    Podcast.status == db_enums.PodcastStatus.ACTIVE,
                    PodcastConfig.enable_show_page.is_(True))
            .order_by(CategoryPodcastMap.priority.desc())
            .all())
    result['podcasts'] = [{
        'id': r.podcast_id,
        'priority': r.priority,
        'title': r.title,
        'imageUrl': r.image_url
    } for r in rows]

    return result


def _replace_category_podcasts(category_id: str, podcasts: dict = None) -> None:
    if not podcasts:
        return

    (db.session.query(CategoryPodcastMap)
     .filter_by(category_id=category_id)
     .delete(synchronize_session=False))

    for p in podcasts:
        db.session.add(CategoryPodcastMap(
            category_id=category_id,
            podcast_id=p['id'],
            priority=p.get('priority', 0)
        ))


def _update_category_podcast_priorities(category_id: str, podcasts: dict = None) -> None:
    if not podcasts:
        return

    for p in podcasts:
        (db.session.query(CategoryPodcastMap)
            .filter_by(category_id=category_id,
                       podcast_id=p['id'])
            .update({
                CategoryPodcastMap.priority: p.get('priority', 0),
                CategoryPodcastMap.updated_at: now()
            }, synchronize_session=False))


def _update_category(category_id: str, body: dict) -> None:
    # Careful not to pass an empty array or else all
    # podcasts in a category could be deleted!
    podcasts = body.pop('podcasts', None)

    try:
        row = (db.session.query(Category, CategoryType.key)
               .join(CategoryType, Category.category_type_id == CategoryType.id)
               .filter(Category.id == category_id)
               .one())
    except NoResultFound:
        raise CategoryNotFound(f'Category {category_id} not found')

    category = row[0]
    category_type = db_enums.CategoryType[row[1]]

    try:
        with db.session.begin_nested():
            for k, v in body.items():
                if hasattr(category, k) and getattr(category, k) != v:
                    setattr(category, k, v)
    except IntegrityError:
        raise CategorySlugTaken(f'Cannot update category {category_id}; '
                                f'slug {body.get("slug")} is already taken')

    if podcasts is not None:
        with db.session.begin_nested():
            if category_type is db_enums.CategoryType.CUSTOM:
                _replace_category_podcasts(category.id, podcasts)
            else:
                _update_category_podcast_priorities(category.id, podcasts)


def _update_category_priority(category_id: str, priority: int) -> None:
    (db.session.query(Category)
     .filter(Category.id == category_id)
     .update({Category.priority: priority}))


@jwt_required
def create_category(body: dict):
    podcasts = body.pop('podcasts', None)
    category_id = str(uuid4())
    row = Category(
        id=category_id,
        slug=body.get('slug'),
        name=body['name'],
        category_type_id=_get_category_type_id(db_enums.CategoryType.CUSTOM.name),
        priority=body.get('priority', 0)
    )
    with db.session.begin_nested():
        try:
            db.session.add(row)
        except IntegrityError:
            # FIXME: Making an assumption here
            return 'Slug already taken', 409

    with db.session.begin_nested():
        _replace_category_podcasts(category_id, podcasts)

    db.session.commit()
    return get_category(category_id)


@jwt_required
def update_category(categoryId, body):
    try:
        _update_category(categoryId, body)
    except InvalidCategoryType as ex:
        return str(ex), 400
    except CategoryNotFound as ex:
        return str(ex), 404
    except CategorySlugTaken as ex:
        return str(ex), 409
    db.session.commit()
    return get_category(categoryId)


@jwt_required
def update_categories(body):
    """Update multiple categories."""
    for category in body:
        category_id = category.pop('id')
        priority = category.pop('priority', 0)
        with db.session.begin_nested():
            _update_category_priority(category_id, priority)
    db.session.commit()
    return get_categories()


@jwt_required
def delete_category(categoryId):
    row = (db.session.query(Category, CategoryType.key)
           .join(CategoryType, Category.category_type_id == CategoryType.id)
           .filter(Category.id == categoryId,
                   Category.deleted.is_(False))
           .one_or_none())
    if not row:
        return 'Not found', 404

    category = row[0]
    category_type = db_enums.CategoryType[row[1]]
    if category_type is not db_enums.CategoryType.CUSTOM:
        return "Can only delete 'CUSTOM' categories", 400

    category.deleted = True
    category.hidden = True
    category.slug = None
    db.session.commit()
