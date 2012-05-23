#from google.appengine.ext import webapp2
#from google.appengine.ext.webapp2.util import run_wsgi_app
import webapp2
from google.appengine.api import users
from google.appengine.ext import db
import logging
import os
import jinja2
import cgi
import datetime
import traffic
from crons import CronJobs

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))

class PageHandler(webapp2.RequestHandler):
    def write_template(self, template_file, **params):
        template = jinja_env.get_template(template_file)
        self.response.out.write(template.render(params))

    def write(self, string):
        self.response.out.write(string)


class MainPage(PageHandler):
    def get_existing_user(self, openid_user):
        logging.info('Getting existing user')
        existing_user = db.GqlQuery('SELECT * FROM User WHERE user_id = :1', 
                str(openid_user.user_id()))
        existing_user = list(existing_user)
        if existing_user:
            logging.info('Existing user user_id: ' + existing_user[0].user_id)
            return existing_user[0]
        logging.info('User doesn\'t exist')

    def create_new_user(self, openid_user):
        logging.info('Creating new user')
        user = User(user_id = openid_user.user_id(), nickname =
                openid_user.nickname(), email = openid_user.email())
        user.put()
        return user

    def get(self):
        self.response.headers['Content-Type'] = 'text/html'

        openid_user = users.get_current_user()
        if openid_user:  # signed in already
            existing_user = self.get_existing_user(openid_user)

            user = None
            if not existing_user:
                user = self.create_new_user(openid_user)
            else:
                user = existing_user

            self.response.out.write('Hello <em>%s</em>! [<a href="%s">sign out</a>]' % (
                    user.nickname, users.create_logout_url(self.request.uri)))

            self.write_template('main_page.html')

            route_data = self.get_user_route_data(user)
            self.write_user_route_data(route_data)

        else:     # let openid_user choose authenticator
            self.response.out.write('Hello world! Sign in at: ')
            self.write('<a href="%s" >login</a><br/>' %
                    users.create_login_url(federated_identity='www.google.com/accounts/o8/id'))

    def get_inputs(self):
        inputs = {}
        args = self.request.arguments()
        for name in args:
            value = self.request.get_all(name)
            if name != 'days':
                inputs[name] = value[0]
            else:
                inputs[name] = value

        return inputs

    def post(self):
        openid_user = users.get_current_user()
        if openid_user:  # signed in already
            existing_user = self.get_existing_user(openid_user)

            user = None
            if not existing_user:
                user = self.create_new_user(openid_user)
            else:
                user = existing_user

            self.response.out.write('Hello <em>%s</em>! [<a href="%s">sign out</a>]' % (
                    user.nickname, users.create_logout_url(self.request.uri)))

            inputs = self.get_inputs()

            errors = self.validate_input(inputs)

            params = {}
            params.update(inputs)
            params.update(errors)

            routes = ''
            if not errors:
                router = traffic.RouteHandler()
                routes = router.get_routes(inputs.get('start'),
                        inputs.get('end'))
            else:
                self.write_template('main_page.html', **params)
                return

            self.write_template('main_page.html', **params)

            route = self.put_route(user, routes[0])
            time = datetime.time(int(inputs['hour']), int(inputs['minute']))
            self.put_alert(route, inputs['days'], time)

            route_data = self.get_user_route_data(user)

            self.write_user_route_data(route_data)


        else:     # TODO: let openid_user choose authenticator
            self.response.out.write('Hello world! Sign in at: ')
            self.write('<a href="%s" >login</a><br/>' %
                    users.create_login_url(federated_identity='www.google.com/accounts/o8/id'))

    def write_user_route_data(self, route_data):
        for route in route_data:
            self.write_route(route['route'])
            for alert in route['alerts']:
                self.write_alert(alert)

    # TODO: Should make objects for user, route, and alarm that's separate from
    # the models? This essentially makes a dict of user and all it's data, no
    # concrete structure like an object.
    def get_user_route_data(self, user):
        user_data = []

        routes = self.get_routes(user)
        routes.reverse()
        for route in routes:
            route_data = {}

            alerts = self.get_alerts(route)
            alerts.reverse()

            route_data['route'] = route
            route_data['alerts'] = alerts

            user_data.append(route_data)

        return user_data

    def put_alert(self, route, days, time):
        alert_model = Alert(route = route, days = days, time = time)
        alert_model.put()
        return alert_model

    def write_route(self, route):
        #self.write(str(route) + '<br />')
        self.write('<b>Start: </b>' + route.start + '<br />')
        self.write('<b>End: </b>' + route.end + '<br />')
        self.write('<b>Name: </b>' + route.name + '<br />')
        self.write('<b>Distance: </b>' + route.distance + '<br />')
        self.write('<b>Duration: </b>' + route.normal_duration + '<br /><br />')

    def write_alert(self, alert):
        #self.write(str(alert) + '<br />')
        self.write('<div style="margin-left: 100px">')
        self.write('<b>Route: </b>' + str(alert.route) + '<br />')
        self.write('<b>Days: </b>' + str(alert.days) + '<br />')
        self.write('<b>Time: </b>' + str(alert.time) + '<br /><br />')
        self.write('</div>')


    def put_route(self, user, route):
        route_model = Route(user = user, start = route.start, end = route.end, name = route.name, distance =
                route.distance, normal_duration = route.normal_duration)
        route_model.put()

        return route_model


    def get_alerts(self, route):
        logging.info('Getting alerts for route: ' + str(route))
        alerts = db.GqlQuery('SELECT * FROM Alert WHERE route = :1',
                route)
        return list(alerts)

    def get_routes(self, user):
        logging.info('Getting routes for user: ' + str(user))
        routes = db.GqlQuery('SELECT * FROM Route WHERE user = :1',
                user)
        return list(routes)

    def validate_input(self, inputs):
        errors = {}
        if not inputs.get('start'):
            errors['start_error'] = 'Required field'
        if not inputs.get('end'):
            errors['end_error'] = 'Required field'
        if not self.is_valid_time(inputs.get('hour'), inputs.get('minute')):
            errors['time_error'] = 'Invalid time'

        return errors

    def is_valid_time(self, hour, minute):
        if not hour or not minute:
            return False
        hour = int(hour)
        minute = int(minute)
        if hour >= 0 and hour <= 23 and\
                minute >= 0 and minute <= 59:
            return True
        return False

    def escape_html(self, string):
            return cgi.escape(string, quote=True)


class User(db.Model):
    user_id = db.StringProperty(required=True)
    nickname = db.StringProperty(required=True)
    email = db.EmailProperty()

class Route(db.Model):
    user = db.ReferenceProperty(User, required=True)
    start = db.StringProperty(required=True)
    end = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    distance = db.StringProperty(required=True)
    normal_duration = db.StringProperty(required=True)
#    traffic_duration = db.StringProperty()
#    traffic_color = db.StringProperty()

class Alert(db.Model):
    route = db.ReferenceProperty(Route, required=True)
    days = db.ListProperty(str, required=True)
    time = db.TimeProperty(required=True)

app = webapp2.WSGIApplication([('/', MainPage),
                            ('/crons', CronJobs)],
                            debug=True)

#def main():
#    webapp2.util.run_wsgi_app(application)

#if __name__ == "__main__":
#    main()
