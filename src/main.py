#from google.appengine.ext import webapp2
#from google.appengine.ext.webapp2.util import run_wsgi_app
import webapp2
from google.appengine.api import users
import logging
import os
import jinja2
import cgi
import datetime
import traffic
import models
from crons import CronJobs

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
JINJA_ENV = jinja2.Environment(loader = jinja2.FileSystemLoader(TEMPLATE_DIR))

class PageHandler(webapp2.RequestHandler):
    def write_template(self, template_file, **params):
        template = JINJA_ENV.get_template(template_file)
        self.response.out.write(template.render(params))

    def write(self, string):
        self.response.out.write(string)

class MainPage(PageHandler):
    def get(self):
        logging.info('Handling GET request')
        self.response.headers['Content-Type'] = 'text/html'

        models_handler = models.ModelsHandler()
        openid_user = users.get_current_user()
        if openid_user:  # signed in already
            existing_user = models_handler.get_existing_user(openid_user)

            user = None
            if not existing_user:
                user = models_handler.create_new_user(openid_user)
            else:
                user = existing_user

            self.response.out.write('Hello <em>%s</em>!\
                    [<a href="%s">sign out</a>]' % (
                    user.nickname, users.create_logout_url(self.request.uri)))

            self.write_template('main_page.html')

            route_data = models_handler.get_user_data(user)
            self.write_user_route_data(route_data)

        else:     # let openid_user choose authenticator
            self.response.out.write('Hello world! Sign in at: ')
            self.write('<a href="%s" >login</a><br />' %
                    users.create_login_url(
                            federated_identity='www.google.com/accounts/o8/id'
                    )
            )

    def post(self):
        logging.info('Handling POST request')
        openid_user = users.get_current_user()
        if openid_user:  # signed in already
            models_handler = models.ModelsHandler()
            existing_user = models_handler.get_existing_user(openid_user)

            user = None
            if not existing_user:
                user = models_handler.create_new_user(openid_user)
            else:
                user = existing_user

            self.response.out.write('Hello <em>%s</em>!\
                    [<a href="%s">sign out</a>]' % (
                    user.nickname, users.create_logout_url(self.request.uri)))

            inputs = self.get_inputs()
            errors = self.get_input_errors(inputs)

            route = None
            if not errors:
                router = traffic.RouteHandler()
                route = router.get_live_route(inputs.get('start'),
                        inputs.get('end'))

                if route:
                    route = models_handler.put_route(user, route)
                    time = datetime.time(int(inputs['hour']), int(inputs['minute']))
                    models_handler.put_alert(route, inputs['days'], time)
                else:
                    errors.update({'route_error': 'No results for this route'})

            params = {}
            params.update(inputs)
            params.update(errors)

            route_data = models_handler.get_user_data(user)
            self.write_template('main_page.html', **params)
            self.write_user_route_data(route_data)

        else:     # TODO: let openid_user choose authenticator
            self.response.out.write('Hello world! Sign in at: ')
            self.write('<a href="%s" >login</a><br/>' %
                    users.create_login_url(
                            federated_identity='www.google.com/accounts/o8/id'
                    )
            )

    def get_inputs(self):
        inputs = {}
        args = self.request.arguments()
        logging.info('Getting request inputs from args: ' + str(args))
        for name in args:
            value = self.request.get_all(name)
            if name != 'days':
                inputs[name] = value[0]
            else:
                inputs[name] = value

        return inputs

    def write_user_route_data(self, route_data):
        logging.info('Writing all user route data')
        for route in route_data:
            self.write_route(route['route'])
            for alert in route['alerts']:
                self.write_alert(alert)


    def write_route(self, route):
        #self.write(str(route) + '<br />')
        self.write('<b>Start: </b>' + route.start + '<br />')
        self.write('<b>End: </b>' + route.end + '<br />')
        self.write('<b>Name: </b>' + route.name + '<br />')
        self.write('<b>Distance: </b>' + route.distance + '<br />')
        self.write('<b>Duration: </b>' + route.normal_duration + '<br /><br />')

    def write_alert(self, alert):
        self.write('<div style="margin-left: 75px">')
        self.write('<b>Days: </b>' + str(alert.days) + '<br />')
        self.write('<b>Time: </b>' + str(alert.time) + '<br /><br />')
        self.write('</div>')

    def get_input_errors(self, inputs):
        logging.info('Getting user input errors if any')
        errors = {}
        if not inputs.get('start'):
            errors['start_error'] = 'Required field'
        if not inputs.get('end'):
            errors['end_error'] = 'Required field'
        if not inputs.get('days'):
            errors['days_error'] = 'Must select at least 1 day'
        if not self.is_valid_time(inputs.get('hour'), inputs.get('minute')):
            errors['time_error'] = 'Invalid time'

        return errors

    def is_valid_time(self, hour, minute):
        logging.info('Validating time given: %s:%s' % (hour, minute))
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


app = webapp2.WSGIApplication([('/', MainPage),
                            ('/crons', CronJobs)],
                            debug=True)

#def main():
#    webapp2.util.run_wsgi_app(application)

#if __name__ == "__main__":
#    main()
