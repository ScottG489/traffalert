#!/usr/bin/python2
import urllib
import re
import sys

def main():
    start = sys.argv[1]
    end = sys.argv[2]

    url_string = 'http://maps.google.com/maps?saddr=%(start)s&daddr=%(end)s' %\
    {'start': start, 'end': end}
    data = urllib.urlopen(url_string).read()
    
    print data
    return

    time_estimate = re.search('In current traffic: ([0-9][0-9])', data).group(1)

    if time_estimate:
        print time_estimate
    else:
        print 'No traffic data'

main()
