from google.appengine.ext import db
import logging

class ModelsHandler(object):
    def get_existing_user(self, openid_user):
        logging.info('Getting existing user if any')
        existing_user = db.GqlQuery('SELECT * FROM User WHERE user_id = :1', 
                str(openid_user.user_id()))
        existing_user = list(existing_user)
        if existing_user:
            logging.info('Got existing user user_id: ' + existing_user[0].user_id)
            return existing_user[0]
        logging.info('User doesn\'t exist')

    def get_alerts(self, route):
        logging.info('Getting alerts for route: ' + str(route))
        alerts = db.GqlQuery('SELECT * FROM Alert WHERE route = :1',
                route)
        return list(alerts)

    def get_routes(self, user):
        logging.info('Getting routes for user: ' + str(user.user_id))
        routes = db.GqlQuery('SELECT * FROM Route WHERE user = :1',
                user)
        return list(routes)

    # TODO: Should make objects for user, route, and alarm that's separate from
    # the models? This essentially makes a dict of user and all it's data, no
    # concrete structure like an object. Also the structure is weird, no actual
    # user information is returned. Review heirarchy.
    def get_user_data(self, user):
        'Get hashmap of user data containing routes and their alerts'
        logging.info('Getting data from given user: ' + user.user_id)
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


    def create_new_user(self, openid_user):
        logging.info('Creating new user')
        user = User(user_id = openid_user.user_id(), nickname =
                openid_user.nickname(), email = openid_user.email())
        user.put()
        return user

    def put_alert(self, route, days, time):
        logging.info('Creating new alert')
        alert_model = Alert(route = route, days = days, time = time)
        alert_model.put()
        return alert_model

    def put_route(self, user, route):
        logging.info('Creating new route')
        route_model = Route(user = user, start = route.start, end = route.end,
                name = route.name, distance = route.distance,
                normal_duration = route.normal_duration)
        route_model.put()

        return route_model

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
