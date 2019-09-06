from argon2 import PasswordHasher
from flask_jwt_extended import jwt_required
from sqlalchemy.sql.functions import count
from sqlalchemy import tuple_
import operator
from cadence13.db.tables import User
from cadence13.api.util.db import db
from cadence13.api.common.schema.db import UserSchema
from cadence13.api.util.logging import get_logger
from cadence13.api.util.pagination import (
    DEFAULT_PAGE_LIMIT,
    SortOrder,
    PageDirection,
    decode_cursor,
    encode_cursor,
)
from cadence13.api.util.string import check_email_validity


logger = get_logger(__name__)
pw_hasher = PasswordHasher()

USERS_DEFAULT_LIMIT = 25


# @jwt_required
def get_users(limit=None, sortOrder=None, nextCursor=None, prevCursor=None):
    limit = limit if limit else USERS_DEFAULT_LIMIT
    next_cursor = nextCursor
    prev_cursor = prevCursor
    sort_order = sortOrder

    cursor = next_cursor or prev_cursor
    page_direction = (PageDirection.FORWARD if not cursor or next_cursor
                      else PageDirection.BACKWARD)
    sort_order = SortOrder[sort_order.upper()] if sort_order else SortOrder.ASC
    reverse_order = (SortOrder.ASC if sort_order is SortOrder.DESC
                     else SortOrder.DESC)

    # Base query never changes
    stmt = db.session.query(User)

    # TODO: Add any filters

    # Fetch total results before pagination and limits
    total = stmt.count()

    # Handle any pagination here. Assume this is
    # the first page and use default sort order
    query_order = sort_order
    if cursor:
        cursor = decode_cursor(cursor)
        # If we're paging backwards, we need to search backwards\
        if prev_cursor:
            query_order = reverse_order
        compare_func = operator.lt if query_order is SortOrder.DESC else operator.gt
        compare_cols = tuple_(User.first_name, User.last_name, User.id)
        compare_vals = tuple_(cursor['firstName'], cursor['lastName'], cursor['id'])
        stmt = stmt.filter(compare_func(compare_cols, compare_vals))

    # Figure out whether to call desc() or asc() on the fly
    stmt = (stmt.order_by(getattr(User.first_name, query_order.name.lower())(),
                          getattr(User.last_name, query_order.name.lower())(),
                          getattr(User.id, query_order.name.lower())()))

    # Fetch an extra row to see if there's more to get
    query_limit = limit + 1
    stmt = stmt.limit(query_limit)

    # Finally perform the query
    rows = stmt.all()
    has_more = len(rows) == query_limit
    if has_more:
        del rows[-1]
    if query_order != sort_order:
        rows.reverse()

    schema = UserSchema(many=True)
    results = schema.dump(rows)

    has_next = prev_cursor or (page_direction is PageDirection.FORWARD and has_more)
    has_prev = next_cursor or (page_direction is PageDirection.BACKWARD and has_more)
    next_cursor = None
    prev_cursor = None
    if has_next:
        next_cursor = encode_cursor(results[-1], ['firstName', 'lastName', 'id',])
    if has_prev:
        prev_cursor = encode_cursor(results[0], ['firstName', 'lastName', 'id',])

    return {
        'data': results,
        'total': total,
        'nextCursor': next_cursor,
        'prevCursor': prev_cursor
    }


@jwt_required
def create_user(body):
    schema = UserSchema()
    deserialized = schema.load(body)
    logger.info(deserialized)

    row = User(
        **deserialized,
        password=pw_hasher.hash('supersecretpassword'),
    )
    db.session.add(row)
    db.session.commit()
    schema = UserSchema()
    result = schema.dump(row)
    return result


@jwt_required
def get_user(userId):
    row = (db.session.query(User)
           .filter(User.id == userId)
           .one_or_none())

    if not row:
        return 'Not found', 404

    schema = UserSchema()
    result = schema.dump(row)
    return result


@jwt_required
def update_user(userId, body):
    row = (db.session.query(User)
           .filter(User.id == userId)
           .one_or_none())

    if not row:
        return 'Not found', 404

    schema = UserSchema()
    deserialized = schema.load(body)
    for k, v in deserialized.items():
        setattr(row, k, v)
    db.session.commit()
    result = schema.dump(row)
    return result


@jwt_required
def delete_user(userId):
    row = (db.session.query(User)
           .filter(User.id == userId)
           .one_or_none())

    if not row:
        return 'Not found', 404

    schema = UserSchema()
    result = schema.dump(row)
    db.session.delete(row)
    db.session.commit()
    return result


def validate_email(body):
    email = body.get('email')
    if not email or not check_email_validity(email):
        return 'Email is invalid', 400
    row = (db.session.query(User)
            .filter(User.email == email)
            .one_or_none())
    if row is None:
        return 'Email is valid', 200
    else:
        return 'Email already exists', 400
