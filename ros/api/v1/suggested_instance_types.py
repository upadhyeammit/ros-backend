from flask import request
from sqlalchemy import func
from flask_restful import Resource, fields, marshal_with
from ros.lib.aws_instance_types import INSTANCE_TYPES

from ros.lib.utils import (
    system_ids_by_org_id,
    org_id_from_identity_header,
)

from ros.lib.models import (
    db,
    PerformanceProfile,
)

from ros.api.common.pagination import (
    limit_value,
    offset_value,
    build_paginated_system_list_response
)


class SuggestedInstanceTypes(Resource):
    data = {
        'instance_type': fields.String,
        'cloud_provider': fields.String,
        'system_count': fields.Integer,
        'description': fields.String,
    }
    meta_fields = {
        'count': fields.Integer,
        'limit': fields.Integer,
        'offset': fields.Integer
    }
    links_fields = {
        'first': fields.String,
        'last': fields.String,
        'next': fields.String,
        'previous': fields.String
    }
    output = {
        'meta': fields.Nested(meta_fields),
        'links': fields.Nested(links_fields),
        'data': fields.List(fields.Nested(data))
    }

    @marshal_with(output)
    def get(self):
        limit = limit_value()
        offset = offset_value()

        query = self.non_null_suggested_instance_types
        count = query.count()
        query = query.limit(limit).offset(offset)
        query_result = query.all()

        suggested_instances = []
        for row in query_result:
            # As of now we only support AWS cloud, so statically adding it to the dict
            record = {'instance_type': row.top_candidate, 'cloud_provider': 'AWS', 'system_count': row.system_count,
                      'description': self.instance_descriptions[row.top_candidate]}
            suggested_instances.append(record)

        return build_paginated_system_list_response(limit, offset, suggested_instances, count)

    @property
    def non_null_suggested_instance_types(self):
        org_id = org_id_from_identity_header(request)
        systems_query = system_ids_by_org_id(org_id)
        return db.session.query(PerformanceProfile.top_candidate,
                                func.count(PerformanceProfile.system_id).label('system_count')).filter(
            PerformanceProfile.top_candidate.is_not(None)).filter(
            PerformanceProfile.system_id.in_(systems_query)).group_by(PerformanceProfile.top_candidate).order_by(
            PerformanceProfile.top_candidate)

    @property
    def instance_descriptions(self):
        instance_and_descriptions = {}
        for instance, info in INSTANCE_TYPES.items():
            processor = info['extra']['physicalProcessor']
            v_cpu = info['extra']['vcpu']
            memory = info['extra']['memory']
            instance_and_descriptions[instance] = f"{processor} instance with {v_cpu} vCPUs and {memory} RAM"
        return instance_and_descriptions
