import json
import functools

from dataikuapi.utils import dku_quote


class DSSCache(object):
    def __init__(self, client, project_key):
        self.client = client
        self.project_key = project_key

    def _entries_to_dict(self, entries):
        entries_dict = {}
        for entry in entries:
            entries_dict[entry['key']['second']] = None if entry['value'] == 'None' else json.loads(entry['value'])
        return entries_dict

    def get_entry(self, key):
        """
        Gets the cache entry if it exists
        Returns the value or raises an exception if entry does not exists
        """
        resp = self.client._perform_raw("GET", "/projects/%s/cache/%s" % (self.project_key, dku_quote(key)))
        if resp.status_code == 200:
            # cache hit
            try:
                return resp.json()
            except:
                raise Exception("DSS response has not the right form")
        elif resp.status_code == 204:
            # cache miss
            raise KeyError
        raise Exception("Unknown error")

    def get_batch(self, keys):
        resp = self.client._perform_json("GET", "/projects/%s/cache/" % self.project_key, body=keys)
        resp['hits'] = self._entries_to_dict(resp['hits'])
        return resp

    def set_entry(self, key, value, ttl=0):
        """
        Sets the cache entry with an optional ttl (defaults to infinite)
        """
        if ttl > 0:
            self.client._perform_raw("POST", "/projects/%s/cache/%s" % (self.project_key, dku_quote(key)),
                                     params={"ttl": ttl}, body=value)
        else:
            self.client._perform_raw("POST", "/projects/%s/cache/%s" % (self.project_key, dku_quote(key)),
                                      body=value)

    def set_entry_batch(self, dict, ttl=0):
        """
        Sets the cache entry with an optional ttl (defaults to infinite)
        """
        if ttl > 0:
            body = [{'key': entry, 'value': str(dict[entry]), 'ttl': ttl} for entry in dict]
        else:
            body = [{'key': entry, 'value': str(dict[entry])} for entry in dict]
        self.client._perform_raw("POST", "/projects/%s/cache/" % (self.project_key), body=body)

    def delete_entry(self, key):
        """
        Deletes the entry
        """
        self.client._perform_raw("DELETE", "/projects/%s/cache/%s" % (self.project_key, dku_quote(key)))

    def delete_cache(self, key):
        """
        Deletes the entry
        """
        self.client._perform_raw("DELETE", "/projects/%s/cache" % self.project_key)

    def cached(self, function_id=None):
        """
        example:
        @dss_cache.cached()
        def double(n):
            return 2*

        or with a custom key prefix
        @dss_cache.cached(function_id='double_val')
        """

        dss_cache = self
        def inner(fun):
            @functools.wraps(fun)
            def inner_inner(*args, **kwargs):
                if (function_id is not None):
                    key = function_id + str(args)
                else:
                    key = fun.__name__ + str(args)
                try:
                    res = dss_cache.get_entry(key)
                    print("got cache hit for: ", key, "\nvalue is : ", res)
                    return res
                except:
                    res = fun(*args, **kwargs)
                    dss_cache.set_entry(key, res)
                    print("writing in cache: ", key, "\nvalue : ", res)
                    return res
            return inner_inner
        return inner
