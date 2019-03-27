import flask
import os

from opencensus.stats.exporters import prometheus_exporter as prometheus
from opencensus.stats.exporters import stackdriver_exporter as stackdriver
from opencensus.stats.exporters.stackdriver_exporter import Options
from flask_middleware import OpenCensusFlask
from decorators import export_response_time

app = flask.Flask(__name__)


'''A more complex flask app making use of middleware and the open census lib to measure metrics in stackdriver'''
middleware = OpenCensusFlask(app, exporter=stackdriver.new_stats_exporter(
    options=Options(project_id=os.getenv('PROJECT_ID'))))


@app.route('/', methods=["GET", "POST"])
@export_response_time
def hello():
    return 'Hello world!'


if __name__ == '__main__':
    app.run(host='localhost', port=8080)
