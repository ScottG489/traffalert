#!/usr/bin/python2
import urllib
import re
import sys
from xml.dom.minidom import *

# TODO: Look into Google web service API's. They don't seem to take traffic data
# into account but may be useful for other features.
# TODO: Improve scraping of traffic data with current method.
# TODO: Add testing! TDD from here forward!
def main():
    start = sys.argv[1]
    end = sys.argv[2]

#    start = '19 kelly ave albany ny'
#    end = '16 sage estates albany ny'
#    temp = start
#    start = end
#    end = temp

    maps_url = 'http://maps.google.com/maps?saddr=%(start)s&daddr=%(end)s' %\
    {'start': start, 'end': end}

    routes = RouteURL.parse(maps_url)

    for route in routes:
        if route.name:
            print route.traffic_duration
        else:
            print 'No traffic raw_map_html'

class RouteURL(object):
    @staticmethod
    def parse(google_maps_url):
        routes_dom = RouteURL._url_to_dom(google_maps_url)

        routes = []

        dom_routes = routes_dom.getElementsByTagName('li')
        for dom_route in dom_routes:
            route = RouteURL._dom_to_Route(dom_route)
            routes.append(route)

        return routes

    @staticmethod
    def _url_to_dom(url):
        raw_map_html = urllib.urlopen(url).read()

        traffic_html = re.search('<ol class="dir-altroute-(mult|sngl) dir-mrgn".*</ol>',
                raw_map_html).group()

        traffic_dom = parseString(traffic_html)

        return traffic_dom

    @staticmethod
    def _dom_to_Route(dom_route):
        route = Route()
        traffic_data_found = False

        route.distance = dom_route.getElementsByTagName('span')[0].\
                firstChild.data
        route.normal_duration = dom_route.getElementsByTagName('span')[1].\
                firstChild.data
        for div in dom_route.getElementsByTagName('div'):
            if div.getAttribute('class') == 'altroute-rcol altroute-aux':
                route.traffic_duration = \
                div.getElementsByTagName('span')[0].firstChild.data.strip()
                traffic_data_found = True
            elif not div.hasAttributes():
                route.name = div.firstChild.data
        if not traffic_data_found:
            route.traffic_duration = u'No traffic information'

        return route


class Route(object):
    def __init__(self):
        self.name = ''
        self.distance = ''
        self.normal_duration = ''
        self.traffic_duration = ''

    def __str__(self):
        return str({'name': self.name, 'distance': self.distance,\
                'normal_duration': self.normal_duration, 'traffic_duration':
                self.traffic_duration})

main()
