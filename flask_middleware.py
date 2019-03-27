import inspect
import flask

from opencensus.common.transports import sync
from opencensus.stats import measure as measure_module
from opencensus.trace import utils
from opencensus.stats import stats
from opencensus.stats import view
from opencensus.stats import aggregation
from opencensus.tags import tag_key as tag_key_module

TRANSPORT = 'TRANSPORT'
BLACKLIST_PATHS = 'BLACKLIST_PATHS'
GCP_EXPORTER_PROJECT = 'GCP_EXPORTER_PROJECT'


class OpenCensusFlask(object):
    def __init__(self, app=None, blacklist_paths=None, exporter=None):
        self.app = app
        self.blacklist_paths = blacklist_paths
        self.exporter = exporter

        stats_stats = stats.Stats()

        self.app.m_response_ms = measure_module.MeasureFloat("flask_response_time", "The request duration", "ms")

        self.app.key_method = tag_key_module.TagKey("method")
        # Create the status key
        self.app.key_status = tag_key_module.TagKey("status")
        # Create the error key
        self.app.key_error = tag_key_module.TagKey("error")

        self.app.view_manager = stats_stats.view_manager

        if self.app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

        params = self.app.config.get('OPENCENSUS_TRACE_PARAMS', {})
        self.blacklist_paths = params.get(BLACKLIST_PATHS,
                                          self.blacklist_paths)

        transport = params.get(TRANSPORT, sync.SyncTransport)

        # Initialize the exporter
        if not inspect.isclass(self.exporter):
            pass  # handling of instantiated exporter
        elif self.exporter.__name__ == 'StackdriverExporter':
            _project_id = params.get(GCP_EXPORTER_PROJECT, None)
            self.exporter = self.exporter(
                project_id=_project_id,
                transport=transport)
        else:
            self.exporter = self.exporter(transport=transport)

        response_time_view = view.View("response_time", "The time it took to respond",
                                       [self.app.key_method, self.app.key_status, self.app.key_error],
                                       self.app.m_response_ms, aggregation.LastValueAggregation())

        self.app.view_manager.register_exporter(self.exporter)
        self.app.view_manager.register_view(response_time_view)

        self.setup_metrics()

    def setup_metrics(self):
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)
        self.app.teardown_request(self._teardown_request)

    def _before_request(self):
        """A function to be run before each request.
        See: http://flask.pocoo.org/docs/0.12/api/#flask.Flask.before_request
        """
        # Do not record stats if the url is blacklisted
        if utils.disable_tracing_url(flask.request.url, self.blacklist_paths):
            return

    def _after_request(self, response):
        # Do not trace if the url is blacklisted
        if utils.disable_tracing_url(flask.request.url, self.blacklist_paths):
            return response

        return response

    def _teardown_request(self, exception):
        # Do not trace if the url is blacklisted
        if utils.disable_tracing_url(flask.request.url, self.blacklist_paths):
            return

