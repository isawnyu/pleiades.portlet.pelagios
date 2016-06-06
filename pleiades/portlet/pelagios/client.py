import logging

import requests
from time import time
from urllib import quote_plus

from pprint import pprint

log = logging.getLogger("pleiades.portlet.pelagios")


class PelagiosAPIError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg


def annotations(pid):
    purl = "http://pleiades.stoa.org/places/" + pid
    escaped = quote_plus(purl)
    results = []
    u = "http://pelagios.org/peripleo/places/" + escaped

    start = time()
    try:
        resp = requests.get(u, timeout=(2, 5))
        log.info('Pelagios request for {} made in {} seconds'.format(
            pid, time() - start))
    except requests.exceptions.RequestException as e:
        raise PelagiosAPIError(repr(e))

    if resp.status_code == 200:
        r = resp.json()
        refs = r.get('referenced_in', [])
        subs = []
        for dataset in refs:
            uri = u'http://pelagios.org/peripleo/map#places={}&datasets={}&f=open'.format(
                escaped, dataset['identifier']
            )
            title = dataset['title']
            if (title == "Pleiades Annotations in the Perseus Digital Library"
                    ) and title != "Greek and Roman Materials":
                continue
            count = dataset['count']
            label = title.rstrip(".")
            subs.append((count, label, uri))
        results.append(
            (len(subs), r['title'], sorted(subs, reverse=True)))
    else:
        raise PelagiosAPIError(repr(resp))
    return sorted(results, reverse=True)

if __name__ == "__main__":
    r = annotations("579885")
    pprint(r)
    print(len(r))
