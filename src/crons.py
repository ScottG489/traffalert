import logging
import webapp2
from models import *
from traffic import *
from google.appengine.ext import db
#from dateutil.rrule import *
from datetime import datetime
from google.appengine.api import mail

class CronJobs(webapp2.RequestHandler):
    def get(self):
        logging.info('\nCRON RUN')

        current_alerts = self.get_alerts_now()
        active_alerts = self.get_active_alerts(current_alerts)

        self.send_alerts(active_alerts)

        for alert in active_alerts:
            self.write_route(alert['live_route'])
            self.write_alert(alert['alert'])

    # XXX: The way the data structure this returns is structured is awkward.
    def get_active_alerts(self, alerts):
        active_alerts = []
        router = RouteHandler()
        for alert in alerts:
            route = alert.route
            live_route = router.get_live_route(route.start, route.end)
            if self.is_route_active(live_route):
                active_alerts.append(
                        {'alert': alert, 'live_route': live_route}
                )

        return active_alerts

    def is_route_active(self, route):
        if route.traffic_color == 'yellow'\
            or route.traffic_color == 'red':
                return True

        return False


    def send_alerts(self, alerts):
        for alert in alerts:
            live_route = alert['live_route']
            alert = alert['alert']
            user = alert.route.user
            body = """
                    There is traffic on your route!
                    Name: %s
                    Start: %s
                    End: %s
                    Traffic Duration: %s
                    Traffic Status: %s
                    """ % (
                            live_route.name, live_route.start,
                            live_route.end, live_route.traffic_duration,
                            live_route.traffic_color
                    )

            mail.send_mail(sender='goldcow64@gmail.com',
                    to=str(user.email),
                    subject='Traffic on ' + live_route.name,
                    body=body)
            logging.info('BODY: ' + body)

    def get_alerts_now(self):
        weekday_today = datetime.now().strftime('%a').upper()[0:2]
        logging.info(weekday_today)

        time_now = datetime.now().time()
        time_now_minute = None
        if time_now.minute == 0:
            time_now_minute = 60
        else:
            time_now_minute = time_now.minute
        minute_before_now = time_now.replace(minute=time_now_minute - 9)#always 1
        logging.info('NOW: ' + str(time_now))
        logging.info('THEN: ' + str(minute_before_now))

        alerts = db.GqlQuery('SELECT * FROM Alert WHERE days = :1\
                AND time < :2 AND time > :3', weekday_today, time_now, minute_before_now)

        return alerts


    def write_route(self, route):
        #self.write(str(route) + '<br />')
        self.write('<b>Start: </b>' + route.start + '<br />')
        self.write('<b>End: </b>' + route.end + '<br />')
        self.write('<b>Name: </b>' + route.name + '<br />')
        self.write('<b>Distance: </b>' + route.distance + '<br />')
        self.write('<b>Duration: </b>' + route.normal_duration + '<br />')
        self.write('<b>Traffic Duration: </b>' + route.traffic_duration + '<br />')
        self.write('<b>Traffic Status: </b>' + route.traffic_color + '<br /><br />')

    def write_alert(self, alert):
        self.write('<div style="margin-left: 75px">')
        self.write('<b>Days: </b>' + str(alert.days) + '<br />')
        self.write('<b>Time: </b>' + str(alert.time) + '<br /><br />')
        self.write('</div>')

    def write(self, string):
        self.response.out.write(string)




        #list(rrule(DAILY, count=3, byweekday=(TU,TH),dtstart=datetime(2007,1,1)))

#        mail.send_mail(sender='goldcow64@gmail.com',
#              to='goldcow64@gmail.com',
#              subject='TEST EMAIL SUBJECT',
#              body='THIS IS A TEST EMAIL BODY')

