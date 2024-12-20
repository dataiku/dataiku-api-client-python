import datetime
import time
import threading

dku_tracing_ls = threading.local()


def new_trace(name):
    return SpanBuilder(name)


def current_span_builder():
    if hasattr(dku_tracing_ls, "current_span_builder"):
        return dku_tracing_ls.current_span_builder
    else:
        return None


def current_span_builder_or_noop():
    if hasattr(dku_tracing_ls, "current_span_builder"):
        return dku_tracing_ls.current_span_builder
    else:
        return SpanBuilder("noop")


class SpanReader(object):
    def __init__(self, data):
        if isinstance(data, SpanBuilder):
            self.span_data = data.span
        else:
            self.span_data = data

    @property
    def name(self):
        return self.span_data["name"]

    @property
    def type(self):
        return self.span_data["type"]

    @property
    def attributes(self):
        return self.span_data["attributes"]

    @property
    def raw_children(self):
        return self.span_data["children"]

    @property
    def children(self):
        for child in self.span_data["children"]:
            child_sr = SpanReader(child)
            yield child_sr

    @property
    def inputs(self):
        return self.span_data.get("inputs", {})

    @property
    def outputs(self):
        return self.span_data.get("outputs", {})

    @property
    def begin(self):
        return self.span_data.get("begin", None)

    @property
    def end(self):
        return self.span_data.get("end", None)

    @property
    def duration(self):
        return self.span_data.get("duration", None)

    @property
    def begin_ts(self):
        return int(datetime.datetime.strptime(self.span_data["begin"], "%Y-%m-%dT%H:%M:%S.%f%z").timestamp() * 1000)

    @property
    def end_ts(self):
        return int(datetime.datetime.strptime(self.span_data["end"], "%Y-%m-%dT%H:%M:%S.%f%z").timestamp() * 1000)


class SpanBuilder:
    def __init__(self,name):
        self.span = {
            "type": "span",
            "name": name,
            "children": [],
            "attributes": {},
            "inputs": {},
            "outputs":  {}
        }

    def to_dict(self):
        if "begin" in self.span and not "end" in self.span:
            self.end(int(time.time() * 1000))
        return self.span

    @property
    def inputs(self):
        if self.span.get("inputs", None) is None:
            self.span["inputs"] = {}
        return self.span["inputs"]

    @property
    def outputs(self):
        if self.span.get("outputs", None) is None:
            self.span["outputs"] = {}
        return self.span["outputs"]

    @property
    def attributes(self):
        return self.span["attributes"]

    def subspan(self, name):
        sub = SpanBuilder(name)
        self.span["children"].append(sub.span)
        return sub

    def append_trace(self, trace_to_append):
        if isinstance(trace_to_append, dict):
            self.span["children"].append(trace_to_append)
        elif isinstance(trace_to_append, SpanBuilder):
            self.span["children"].append(trace_to_append.to_dict())
        else:
            raise Exception("Cannot happen trace of type %s" % type(trace_to_append))

    def begin(self, begin_time):
        self._begin_ts = begin_time
        self.span["begin"] = datetime.datetime.utcfromtimestamp(begin_time / 1000).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def end(self, end_time):
        self.span["end"] = datetime.datetime.utcfromtimestamp(end_time / 1000).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        #print("Ending span: %s -> %s" % (self.span["begin"], self.span["end"]))
        self.span["duration"] = int(end_time - self._begin_ts)

    def __enter__(self,):
        self.previous_sb_on_thread = current_span_builder()
        dku_tracing_ls.current_span_builder = self
        self.begin(int(time.time() * 1000))
        return self

    def __exit__(self, type, value, traceback):
        dku_tracing_ls.current_span_builder = self.previous_sb_on_thread
        self.previous_sb_on_thread = None
        self.end(int(time.time() * 1000))


def mini_trace_dump(trace):
    def _rec(span, level):
        print("%s %s (%s -> %s: %s)" % ("  "* (2 * level), span.name, span.begin, span.end, span.duration))
        for child in span.children:
            _rec(child, level +1)

    _rec(SpanReader(trace), 0)