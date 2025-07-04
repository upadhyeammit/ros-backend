import json
import logging
from flask import request
from flask_restful import abort
from ros.lib.models import System, RatingChoicesEnum
from ros.lib.utils import (
    identity,
    user_data_from_identity,
    is_valid_uuid,
    system_ids_by_org_id,
    service_account_from_identity
)
from ros.extensions import db
from sqlalchemy import exc
from ros.api.common.add_group_filter import group_filtered_query
from sqlalchemy import asc, desc

LOG = logging.getLogger(__name__)
prefix = "VALIDATE REQUEST"


def validate_rating_data(func):
    """Validate POST rating request."""
    allowed_choices = [c.value for c in RatingChoicesEnum]

    def error_msg(error_code, value):
        errors = {
            400: "is invalid value for rating.",
            422: "is invalid choice of input for rating."
        }
        return (
            f"'{value}' {errors.get(error_code, 'Invalid')}"
            f" Possible values - {*allowed_choices, }"
        )

    def check_for_rating(data):
        rating = None
        try:
            rating = int(data['rating'])
        except ValueError:
            abort(400, message=(error_msg(400, data['rating'])))

        if rating not in allowed_choices:
            abort(422, message=(error_msg(422, data['rating'])))

        return rating

    def check_for_user():
        username = None
        ident = identity(request)['identity']
        user = user_data_from_identity(ident)
        service_account_info = service_account_from_identity(ident)
        if isinstance(user, dict):
            username = user.get('username')
        elif isinstance(service_account_info, dict):
            username = service_account_info.get('username')

        if username is None:
            abort(403, message="Username doesn't exist")

        return ident, username

    def check_for_system(ident, inventory_id):
        system_id = None
        if not is_valid_uuid(inventory_id):
            abort(404, message='Invalid inventory_id, Id should be in form of UUID4')
        systems = group_filtered_query(system_ids_by_org_id(ident['org_id']).
                                       filter(System.inventory_id == inventory_id))
        try:
            system_id = db.session.execute(systems).scalar_one()
        except exc.NoResultFound:
            abort(404, message=f"System {inventory_id} doesn't exist.")

        return system_id

    def validate_request(*args, **kwargs):
        ident, username = check_for_user()
        data = None
        try:
            data = json.loads(request.data)
        except json.decoder.JSONDecodeError as err:
            LOG.error(f"{prefix} - Decoding JSON has failed. {repr(err)}")
            abort(400, message="Decoding JSON has failed.")
        except TypeError as ex:
            LOG.error(f"{prefix} - Invalid JSON format. {repr(ex)}")
            abort(400, message="Invalid JSON format.")

        inventory_id = data['inventory_id']
        system_id = check_for_system(ident, inventory_id)

        rating = check_for_rating(data)
        new_kwargs = {
            'rating': rating, 'username': username,
            'inventory_id': inventory_id, 'system_id': system_id
        }
        new_kwargs.update(kwargs)
        return func(*args, **new_kwargs)

    return validate_request


def sorting_order(order_how):
    """Sorting order method."""
    method_name = None
    if order_how == 'asc':
        method_name = asc
    elif order_how == 'desc':
        method_name = desc
    else:
        abort(
            403,
            message="Incorrect sorting order. Possible values - ASC/DESC"
        )
    return method_name
