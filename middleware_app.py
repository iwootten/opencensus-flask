import flask
import os

from opencensus.ext.stackdriver import stats_exporter as stackdriver
from opencensus.stats import measure as measure_module
from opencensus.stats import aggregation
from decorators import export_response_time
from opencensus.stats import stats
from opencensus.stats import view
from opencensus.tags import tag_key as tag_key_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.tags import tag_value as tag_value_module
from flask_middleware import OpenCensusFlask

app = flask.Flask(__name__)


def setup_open_census():
    stats_stats = stats.Stats()

    app.m_response_ms = measure_module.MeasureFloat("flask_response_time", "The request duration", "ms")

    app.key_method = tag_key_module.TagKey("method")
    # Create the status key
    app.key_status = tag_key_module.TagKey("status")
    # Create the error key
    app.key_error = tag_key_module.TagKey("error")

    app.view_manager = stats_stats.view_manager
    app.stats_recorder = stats_stats.stats_recorder
    response_time_view = view.View("response_time", "The time it took to respond",
                                   [app.key_method, app.key_status, app.key_error],
                                   app.m_response_ms, aggregation.LastValueAggregation())

    app.exporter = stackdriver.new_stats_exporter(options=stackdriver.Options(project_id=os.getenv('PROJECT_ID')))

    app.view_manager.register_exporter(app.exporter)
    app.view_manager.register_view(response_time_view)


'''A more complex flask app making use of middleware and the open census lib to measure metrics in stackdriver'''
middleware = OpenCensusFlask(app, exporter=stackdriver.new_stats_exporter(options=stackdriver.Options(project_id=os.getenv('PROJECT_ID'))))


@app.route('/', methods=["GET", "POST"])
@export_response_time
def hello():
    return 'Hello world!'


if __name__ == '__main__':
    app.run(host='localhost', port=8080)
