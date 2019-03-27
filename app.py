from flask import Flask, g
from opencensus.stats.exporters import prometheus_exporter as prometheus
from opencensus.stats import measure as measure_module
from opencensus.stats import aggregation
from opencensus.stats import view
from opencensus.stats import stats
from opencensus.tags import tag_key as tag_key_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.tags import tag_value as tag_value_module
import time

'''A simple flask app making use of the open census lib to measure metrics in prometheus'''

m_response_ms = measure_module.MeasureFloat("flask_response_time", "The request duration", "ms")

key_method = tag_key_module.TagKey("method")
# Create the status key
key_status = tag_key_module.TagKey("status")
# Create the error key
key_error = tag_key_module.TagKey("error")

app = Flask(__name__)


def setup_open_census():
    stats_stats = stats.Stats()
    app.view_manager = stats_stats.view_manager
    app.stats_recorder = stats_stats.stats_recorder
    response_time_view = view.View("response_time", "The time it took to respond",
                                   [key_method, key_status, key_error],
                                   m_response_ms, aggregation.LastValueAggregation())

    app.exporter = prometheus.new_stats_exporter(prometheus.Options(namespace="flask_app", port=8000))

    app.view_manager.register_exporter(app.exporter)
    app.view_manager.register_view(response_time_view)


@app.route('/')
def hello():
    return 'Hello World!'


@app.before_request
def before_request():
    g.request_start_time = time.time() * 1000


@app.after_request
def after_request(response):
    tmap = tag_map_module.TagMap()
    tmap.insert(key_method, tag_value_module.TagValue("get"))
    tmap.insert(key_status, tag_value_module.TagValue("200 OK"))
    mmap = app.stats_recorder.new_measurement_map()
    response_time = time.time() * 1000 - g.request_start_time
    mmap.measure_float_put(m_response_ms, response_time)

    print(response_time)

    mmap.record(tmap)

    return response


if __name__ == '__main__':
    setup_open_census()
    app.run(host='localhost', port=8080, threaded=True)
