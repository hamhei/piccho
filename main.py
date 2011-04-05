#!/usr/bin/env python

import cgi
import datetime
import logging
import os
import math

from google.appengine.dist import use_library
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import images
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from getimageinfo import getImageInfo

#use_library('django', '1.2')
#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
logging.getLogger().setLevel(logging.DEBUG)
tag = "no tag"
name = "no name"

class Greeting(db.Model):
	author = db.StringProperty(multiline=False)
	content = db.StringProperty(multiline=True)
	avatar = db.BlobProperty()
	tag = db.StringProperty(multiline=False)
	date = db.DateTimeProperty(auto_now_add=True)

class Tweet(db.Model):
	img = db.StringProperty(multiline=False)
	content = db.StringProperty(multiline=False)
	author = db.StringProperty(multiline=False)
	date = db.DateTimeProperty(auto_now_add=True)

class LoginPage(webapp.RequestHandler):
	def get(self):
		global tag, name
		tag = "no tag"
		name = "no name"
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		template_empty = {}
		self.response.out.write(template.render(path, template_empty))

class MainPage(webapp.RequestHandler):
	def get(self):
		global tag,name
		#greetings = db.GqlQuery("SELECT * FROM Greeting WHERE tag = :1 ORDER BY date ASC", tag)
		greetings = Greeting.gql("WHERE tag = :1 ORDER BY date ASC", tag)
		names = set([])
		for greeting in greetings:
			names |= set([greeting.author])
		menbers = list(names)
		menbers.sort()
		template_value = {
			'greetings': greetings,
			'tag': tag,
			'name': name,
			'menbers': menbers,
			}
		path2 = os.path.join(os.path.dirname(__file__), 'main.html')
		self.response.out.write(template.render(path2, template_value))

class Image (webapp.RequestHandler):
	def get(self):
		greeting = db.get(self.request.get("img_id"))
		if greeting.avatar:
			self.response.headers['Content-Type'] = "image/png"
			self.response.out.write(greeting.avatar)
		else:
			self.response.out.write("No image")

class Guestbook(webapp.RequestHandler):
	def post(self):
		global tag,name
		greeting = Greeting()
		greeting.tag = tag
		greeting.author = name
		#bug.... sometime missing tag and name.  why?
		 #fix ed!!
		greeting.content = self.request.get("content") + " (by " + name + ")"
		bin=db.Blob(self.request.get("img"))
		content_type, width, height = getImageInfo(bin)
		if width > 600:
			avatar = images.resize(self.request.get("img"), width=600)
		else:
			avatar = self.request.get("img")
		greeting.avatar = db.Blob(avatar)
		greeting.put()
		self.redirect('/main')

class Phrase(webapp.RequestHandler):
	def post(self):
		global tag,name
		tag = self.request.get("tag")
		if self.request.get("name"):
			name = self.request.get("name")
		else:
			name = "no name"
		self.redirect('/main')

class Change(webapp.RequestHandler):
	def post(self):
		global tag
		greetings = Greeting.gql("WHERE tag = :1 ORDER BY date ASC", tag)
		for greeting in greetings:
			greeting.tag = self.request.get("newtag")
			greeting.put()
			tag = self.request.get("newtag")
		self.redirect('/main')

class Comment(webapp.RequestHandler):
	def post(self):
		global tag, name
		greeting = db.get(self.request.get("key"))
		greeting.content = greeting.content + "<br>  " + self.request.get("comment") + " (by " + name + ")"
		greeting.put()
		self.redirect('/main')

class Forgot(webapp.RequestHandler):
	def post(self):
		greetings = Greeting.gql("WHERE author = :1 ORDER BY date ASC", self.request.get("name"))
		tags = set([])
		for greeting in greetings:
			tags |= set([greeting.tag])
		chars = []
		for t in tags:
			chars.append(t[:2])
		template_value = {
			'name': self.request.get("name"),
			'tags': tags,
			'chars': chars,
			}
		path2 = os.path.join(os.path.dirname(__file__), 'forgot.html')
		self.response.out.write(template.render(path2, template_value))

class Rmimg(webapp.RequestHandler):
	def post(self):
		greeting = db.get(self.request.get("key"))
		db.delete(greeting)
		self.redirect("/main")

application = webapp.WSGIApplication([
		('/', LoginPage),
		('/main', MainPage),
		('/img', Image),
		('/sign', Guestbook),
		('/phrase', Phrase),
		('/change', Change),
		('/comment', Comment),
		('/forgot', Forgot),
		('/rmimg', Rmimg)
		], debug=True)

def main():
	run_wsgi_app(application)

if __name__ == '__main__':
	main()
