import logging

import json
from time import time

from Acquisition import aq_inner, aq_parent
from zope.publisher.browser import BrowserView

from Products.PleiadesEntity.content.interfaces import ILocation, IName, IPlace
from pleiades.portlet.pelagios import client
from plone.memoize import ram
from plone.memoize.volatile import DontCache

log = logging.getLogger("pleiades.portlet.pelagios")


def _pelagios_cache_key(method, self, pid):
    if pid:
        # Ten minute RAM cache on API request
        cache_time = time() // (10 * 60)
        return '{}/{}'.format(pid, cache_time)
    else:
        raise DontCache


class RelatedPelagiosJson(BrowserView):

    """Makes one Pelagios Flickr API call and writes data to be used in a
    portal template."""

    @ram.cache(_pelagios_cache_key)
    def _get_annotations(self, pid):
        try:
            annotations = client.annotations(pid)
        except client.PelagiosAPIError as e:
            annotations = None
            log.exception("Pelagios API Error: %s", str(e))
        return annotations

    def __call__(self, **kw):
        data = {}
        context = self.context

        if IPlace.providedBy(context):
            pid = context.getId()  # local id like "149492"
        elif ILocation.providedBy(context) or IName.providedBy(context):
            pid = aq_parent(aq_inner(context)).getId()
        else:
            pid = None

        if pid is not None:
            annotations = self._get_annotations(pid)
            if annotations is None:
                self.request.response.setStatus(500)
                annotations = []
            else:
                self.request.response.setStatus(200)
        else:
            annotations = []
            self.request.response.setStatus(404)

        data = dict(
            pid=pid,
            annotations=annotations)

        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps(data)
