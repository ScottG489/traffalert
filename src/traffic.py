#!/usr/bin/python2
import urllib
import re
import sys
import logging
from xml.dom.minidom import parseString


# TODO: Look into Google web service API's. They don't seem to take traffic data
# into account but may be useful for other features.
# TODO: Improve scraping of traffic data with current method.
# TODO: Add testing! TDD from here forward!
# TODO: Add a 'color' member to the Route object using Google's indicated
# traffic status color.
def main():
    start = sys.argv[1]
    end = sys.argv[2]

#    start = '19 kelly ave albany ny'
#    end = '16 sage estates albany ny'
#    temp = start
#    start = end
#    end = temp


    #routes = RouteHandler.get_routes(maps_url)
    router = RouteHandler()
    routes = router.get_routes(start, end)

    for route in routes:
        if route.name:
            print route
        else:
            print 'No traffic raw_map_html'

class RouteHandler(object):
    def __init__(self):
        self.google_maps_url = 'http://maps.google.com/maps?saddr=%(start)s&daddr=%(end)s'

    def get_routes(self, start, end):
        logging.info('Looking for routes from %s to %s' % (start, end))
        routes_dom = self._url_to_dom(self.google_maps_url % 
                {'start': start, 'end': end})

        if not routes_dom:
            return None

        dom_routes = routes_dom.getElementsByTagName('li')
        routes = []
        for dom_route in dom_routes:
            route = self._dom_to_Route(dom_route)
            route.start = start
            route.end = end

            routes.append(route)

        return routes

    def get_live_route(self, start, end):
        routes = self.get_routes(start, end)
        if routes:
            return self.get_routes(start, end)[0]

    def _url_to_dom(self, url):
        raw_map_html = urllib.urlopen(url).read()

        traffic_html = re.search(
                '<ol class="dir-altroute-(mult|sngl) dir-mrgn".*</ol>',
                raw_map_html)

        if traffic_html:
            traffic_html = traffic_html.group()
            traffic_dom = parseString(traffic_html)

            return traffic_dom

    def _dom_to_Route(self, dom_route):
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

                for item in div.getElementsByTagName('img'):
                    route.traffic_color = re.search(
                            '^dir-traffic dir-traffic-(.*)',
                            item.getAttribute('class')).group(1)

            elif not div.hasAttributes():
                route.name = div.firstChild.data
        if not traffic_data_found:
            route.traffic_duration = u'No traffic information'
            route.traffic_color = u'gray'

        return route


class Route(object):
    def __init__(self):
        self.start = ''
        self.end = ''
        self.name = ''
        self.distance = ''
        self.normal_duration = ''
        self.traffic_duration = ''
        self.traffic_color = ''

    def __str__(self):
        return str({'start': self.start, 'end': self.end, 'name': self.name,
            'distance': self.distance, 'normal_duration': self.normal_duration,
            'traffic_duration': self.traffic_duration,
            'traffic_color': self.traffic_color})

if __name__ == '__main__':
    main()
