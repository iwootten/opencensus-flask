import flask

from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace import execution_context
from opencensus.ext.stackdriver.trace_exporter import StackdriverExporter
from opencensus.common.transports.async_ import AsyncTransport

from decorators import capture_trace

import os


app = flask.Flask(__name__)

se = StackdriverExporter(project_id=os.getenv('PROJECT_ID'), transport=AsyncTransport)

# Enable tracing the requests
middleware = FlaskMiddleware(app, exporter=se)


@capture_trace
def something():
    for i in range(1, 1000):
        print("Some stuff")


@capture_trace
def something_else():
    for i in range(1, 100000):
        print("Some other stuff")


@app.route('/')
def hello():
    tracer = execution_context.get_opencensus_tracer()

    something()

    something_else()

    with tracer.span(name="hello()") as span:
        span.add_attribute("Some attribute", 10)
        return 'Hello world!'


if __name__ == '__main__':
    app.run(host='localhost', port=8080)
