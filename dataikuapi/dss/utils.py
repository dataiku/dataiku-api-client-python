import os, sys, json, logging, traceback

class DSSDatasetSelectionBuilder(object):
    """Builder for a "dataset selection". In DSS, a dataset selection is used to select a part of a dataset for processing.

    Depending on the location where it is used, a selection can include:
    * Sampling
    * Filtering by partitions (for partitioned datasets)
    * Filtering by an expression
    * Selection of columns
    * Ordering

    Please see the sampling documentation of DSS for a detailed explanation of the sampling methods.

    """
    def __init__(self):
        self.selection = {}

    def build(self):
        """Returns the built selection dict"""
        return self.selection

    def with_head_sampling(self, limit):
        """Sets the sampling to 'first records' mode"""
        self.selection["samplingMethod"] = "HEAD_SEQUENTIAL"
        self.selection["maxRecords"] = limit
        return self

    def with_all_data_sampling(self):
        """Sets the sampling to 'no sampling, all data' mode"""
        self.selection["samplingMethod"] = "FULL"
        return self

    def with_random_fixed_nb_sampling(self, nb):
        """Sets the sampling to 'Random sampling, fixed number of records' mode"""
        self.selection["samplingMethod"] = "RANDOM_FIXED_NB"
        self.selection["maxRecords"] = nb
        return self

    def with_selected_partitions(self, ids):
        """Sets partition filtering on the given partition identifiers. The dataset to select must be partitioned."""
        self.selection["partitionSelectionMethod"] = "SELECTED"
        self.selection["selectedPartitions"] = ids
        return self


class DSSFilterBuilder(object):
    """
    Builder for a "filter". In DSS, a filter is used to define a subset of rows for processing.
    """
    def __init__(self):
        self.filter = {"enabled":False, "distinct":False, "expression":None, "uiData":{"mode":"CUSTOM"}}

    def build(self):
        """Returns the built filter dict"""
        return self.filter

    def with_distinct(self):
        """Sets the filter to deduplicate"""
        self.filter["distinct"] = True
        return self

    def with_formula(self, expression):
        """Sets the formula (DSS formula) used to filter rows"""
        self.filter["enabled"] = True
        self.filter["expression"] = expression
        self.filter["uiData"]["mode"] = "CUSTOM"
        return self

########################################################
# helper to find proxy user if relevant
########################################################
_in_flask = None
_in_bokeh = None
_cookie_to_identifier = {}

def _try_get_flask_headers():
    global _in_flask
    if _in_flask is None or _in_flask == True:
        try:
            from flask import request as flask_request
            h = dict(flask_request.headers)
            _in_flask = True
            logging.info("got headers from flask")
            return h
        except:
            # no flask
            _in_flask = False # so that you don't try importing all the time
    return None

def _try_get_bokeh_headers():
    global _in_bokeh
    if _in_bokeh is None or _in_bokeh == True:
        try:
            from bokeh.io import curdoc as bokeh_curdoc
            session_id = bokeh_curdoc().session_context.id
            # nota: this import will fail for a bokeh webapp not run from DSS. But it's fine
            from dataiku.webapps.run_bokeh import get_session_headers as get_bokeh_session_headers
            h = get_bokeh_session_headers().get(session_id, {})
            _in_bokeh = True
            logging.info("got headers from bokeh")
            return h
        except:
            # no bokeh
            _in_bokeh = False # so that you don't try importing all the time
    return None

def _fetch_identifier_from_cookie(client, cookie):
    logging.info("fetching from cookie")
    # by the very definition of this call, it cannot be impersonated, so we flag it as such for the backend
    client._session.headers['X-DKU-NoProxyUser'] = 'true'
    try:
        auth_info = client.get_auth_info_from_browser_headers({"Cookie":cookie})
        return auth_info["authIdentifier"]
    finally:
        del client._session.headers['X-DKU-NoProxyUser']
    return None

def _try_get_identifier_from_cookie(client, call_headers):
    global _cookie_to_identifier
    cookie = call_headers.get("Cookie", call_headers.get("cookie", None))
    if cookie is not None:
        if cookie not in _cookie_to_identifier:
            try:
                _cookie_to_identifier[cookie] = _fetch_identifier_from_cookie(client, cookie)
            except:
                logging.warn("Unable to get identifier from cookie")
        return _cookie_to_identifier.get(cookie, None)
    return None

def _try_get_proxy_user(client):
    # prevent infinite recursion
    if 'X-DKU-NoProxyUser' in client._session.headers:
        return None
    if os.environ.get("DKU_IMPERSONATE_CALLS", '') == 'true':
        # fetch cookies from where you find something
        call_headers = None
        if call_headers is None:
            # try flask 
            call_headers = _try_get_flask_headers()
        if call_headers is None:
            # try bokeh
            call_headers = _try_get_bokeh_headers()
            
        if call_headers is not None:
            # get DSS identity of caller (cache by cookie)
            return _try_get_identifier_from_cookie(client, call_headers)
    return None
