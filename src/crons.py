import logging
import webapp2
#from google.appengine.api import mail

class CronJobs(webapp2.RequestHandler):
    def get(self):
        logging.info('\nCRON RUN')
#        mail.send_mail(sender='goldcow64@gmail.com',
#              to='goldcow64@gmail.com',
#              subject='TEST EMAIL SUBJECT',
#              body='THIS IS A TEST EMAIL BODY')
