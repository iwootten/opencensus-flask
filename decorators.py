from functools import wraps
from flask import current_app, request, make_response
import time

from opencensus.tags import tag_map as tag_map_module
from opencensus.tags import tag_value as tag_value_module
from opencensus.stats import stats


def export_response_time(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request_start_time = time.time() * 1000

        current_app.stats_recorder = stats.Stats().stats_recorder
        response = make_response(f(*args, **kwargs))

        tmap = tag_map_module.TagMap()
        tmap.insert(current_app.key_method, tag_value_module.TagValue(request.method))
        tmap.insert(current_app.key_status, tag_value_module.TagValue(response.status))

        mmap = current_app.stats_recorder.new_measurement_map()

        response_time = time.time() * 1000 - request_start_time

        mmap.measure_float_put(current_app.m_response_ms, response_time)

        print(response_time)

        mmap.record(tmap)

        return response

    return decorated_function
