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
	#when launching, remove "content" parameter
	content = db.StringProperty(multiline=True)
	avatar = db.BlobProperty()
	tag = db.StringProperty(multiline=False)
	date = db.DateTimeProperty(auto_now_add=True)

class Tweet(db.Model):
	content = db.StringProperty(multiline=False)
	author = db.StringProperty(multiline=False)
	date = db.DateTimeProperty(auto_now_add=True)
	img = db.StringProperty(multiline=False)

class LoginPage(webapp.RequestHandler):
	def get(self):
		global tag, name
		tag = "no tag"
		name = "no name"
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		template_value = {}
		self.response.out.write(template.render(path, template_value))

class MainPage(webapp.RequestHandler):
	def get(self):
		global tag,name
		#greetings = db.GqlQuery("SELECT * FROM Greeting WHERE tag = :1 ORDER BY date ASC", tag)
		greetings = Greeting.gql("WHERE tag = :1 ORDER BY date ASC", tag)

		tweets_list = []
		for greeting in greetings:
			temps = Tweet.gql("WHERE img = :1 ORDER BY date ASC", str(greeting.key()))
			tweets_list.append(temps)

		lists = zip(greetings, tweets_list)

		names = set([])
		for greeting in greetings:
			names |= set([greeting.author])
		menbers = list(names)
		menbers.sort()

		template_value = {
			'tag': tag,
			'name': name,
			'menbers': menbers,
			'lists': lists,
			}
		path = os.path.join(os.path.dirname(__file__), 'main.html')
		self.response.out.write(template.render(path, template_value))

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
		#bug.... sometime missing tag and name.  why?
		tag = self.request.get("tag")
		name = self.request.get("name")
		greeting.tag = tag
		greeting.author = name
		bin=db.Blob(self.request.get("img"))
		content_type, width, height = getImageInfo(bin)
		if width > 600:
			avatar = images.resize(self.request.get("img"), width=600)
		else:
			avatar = self.request.get("img")
		greeting.avatar = db.Blob(avatar)
		greeting.put()

		tweet = Tweet()
		tweet.img = str(greeting.key())
		tweet.content = self.request.get("content")
		tweet.author = name
		tweet.put()

		self.redirect('/main')

class Phrase(webapp.RequestHandler):
	def post(self):
		global tag,name
		if self.request.get("tag"):
			tag = self.request.get("tag")
		if self.request.get("name"):
			name = self.request.get("name")
		self.redirect('/main')

class Change(webapp.RequestHandler):
	def post(self):
		global tag
		greetings = Greeting.gql("WHERE tag = :1", tag)
		for greeting in greetings:
			greeting.tag = self.request.get("newtag")
			greeting.put()
			tag = self.request.get("newtag")
		self.redirect('/main')

class Comment(webapp.RequestHandler):
	def post(self):
		global tag, name
		name = self.request.get("name")
		tag = self.request.get("tag")
		tweet = Tweet()
		tweet.img = str(self.request.get("key"))
		tweet.content = self.request.get("comment")
		tweet.author = name
		tweet.put()
		self.redirect('/main')

class Forgot(webapp.RequestHandler):
	def post(self):
		greetings = Greeting.gql("WHERE author = :1 ORDER BY date ASC", self.request.get("name"))
		tags = set([])
		for greeting in greetings:
			tags |= set([greeting.tag])
		chars = []
		length =[]
		for t in tags:
			chars.append(t[:2])
			length.append( "x" * (len(t)-2))
		lists = zip(chars, length)
		template_value = {
			'name': self.request.get("name"),
			'tags': tags,
			'lists': lists,
			}
		path = os.path.join(os.path.dirname(__file__), 'forgot.html')
		self.response.out.write(template.render(path, template_value))

class Rmimg(webapp.RequestHandler):
	def post(self):
		greeting = db.get(self.request.get("key"))
		tweets = Tweet.gql("WHERE img = :1 ", str(self.request.get("key")))
		db.delete(greeting)
		db.delete(tweets)
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
