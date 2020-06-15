from collections import OrderedDict
from functools import lru_cache
from uuid import uuid4

from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

import cadence13.db.enums.values as db_enums
from cadence13.api.util.db import db
from cadence13.api.util.logging import get_logger
from cadence13.db.tables import Category, CategoryPodcastMap, CategoryType, Podcast

logger = get_logger(__name__)


@lru_cache()
def _get_category_type_id(key):
    return db.session.query(CategoryType.id).filter_by(key=key).scalar()


@jwt_required
def get_categories():
    rows = (db.session.query(Category, CategoryType.key)
            .join(CategoryType, Category.category_type_id == CategoryType.id)
            .filter(Category.is_active == True,
                    CategoryType.is_active == True)
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
            'podcasts': []
        }

    rows = (db.session.query(CategoryPodcastMap.category_id,
                             CategoryPodcastMap.podcast_id,
                             CategoryPodcastMap.priority,
                             Podcast.title,
                             Podcast.image_url)
            .join(Category, Category.id == CategoryPodcastMap.category_id)
            .join(Podcast, Podcast.id == CategoryPodcastMap.podcast_id)
            .filter(Category.is_active == True,
                    Podcast.status == db_enums.PodcastStatus.ACTIVE)
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
                   Category.is_active == True,
                   CategoryType.is_active == True)
           .one_or_none())
    if not row:
        return 'Not found', 404

    category, category_type = row
    result = {
        'id': category.id,
        'slug': category.slug,
        'priority': category.priority,
        'name': category.name,
        'type': category_type
    }

    rows = (db.session.query(CategoryPodcastMap.podcast_id,
                             CategoryPodcastMap.priority,
                             Podcast.title,
                             Podcast.image_url)
            .join(Podcast, Podcast.id == CategoryPodcastMap.podcast_id)
            .filter(CategoryPodcastMap.category_id == categoryId,
                    Podcast.status == db_enums.PodcastStatus.ACTIVE)
            .order_by(CategoryPodcastMap.priority.desc())
            .all())
    result['podcasts'] = [{
        'id': r.podcast_id,
        'priority': r.priority,
        'title': r.title,
        'imageUrl': r.image_url
    } for r in rows]

    return result


@jwt_required
def create_category(body: dict):
    category_id = str(uuid4())
    row = Category(
        id=category_id,
        slug=body.get('slug'),
        name=body['name'],
        category_type_id=_get_category_type_id(db_enums.CategoryType.CUSTOM.name),
        priority=body.get('priority', 0)
    )
    try:
        db.session.add(row)
        db.session.commit()
    except IntegrityError:
        return 'Slug already taken', 409

    return get_category(category_id)


def _update_category_podcasts(category_id, podcasts):
    (db.session.query(CategoryPodcastMap)
     .filter_by(category_id=category_id)
     .delete())

    for p in podcasts:
        db.session.add(CategoryPodcastMap(
            category_id=category_id,
            podcast_id=p['id'],
            priority=p.get('priority', 0)
        ))


@jwt_required
def update_category(categoryId, body):
    podcasts = body.pop('podcasts', [])

    row = (db.session.query(Category, CategoryType.key)
           .join(CategoryType, Category.category_type_id == CategoryType.id)
           .filter(Category.id == categoryId)
           .one_or_none())
    if not row:
        return 'Not found', 404

    category = row[0]
    category_type = db_enums.CategoryType[row[1]]
    if category_type is not db_enums.CategoryType.CUSTOM:
        return "Can only update 'CUSTOM' categories", 400

    try:
        with db.session.begin_nested():
            for k, v in body.items():
                if hasattr(category, k):
                    setattr(category, k, v)
    except IntegrityError:
        return 'Slug already taken', 409

    with db.session.begin_nested():
        _update_category_podcasts(category.id, podcasts)

    db.session.commit()
    return get_category(categoryId)


@jwt_required
def delete_category(categoryId):
    row = (db.session.query(Category, CategoryType.key)
           .join(CategoryType, Category.category_type_id == CategoryType.id)
           .filter(Category.id == categoryId,
                   Category.is_active == True)
           .one_or_none())
    if not row:
        return 'Not found', 404

    category = row[0]
    category_type = db_enums.CategoryType[row[1]]
    if category_type is not db_enums.CategoryType.CUSTOM:
        return "Can only delete 'CUSTOM' categories", 400

    category.is_active = False
    category.slug = None
    db.session.commit()
