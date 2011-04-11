#!/usr/bin/env python

import cgi
import datetime
import logging
import os
import math
import appengine_utilities.sessions

from google.appengine.dist import use_library
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import images
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from getimageinfo import getImageInfo
from appengine_utilities.sessions import Session

#use_library('django', '1.2')
#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
logging.getLogger().setLevel(logging.DEBUG)
#tag = "no tag"
#name = "no name"
session = Session()

class Greeting(db.Model):
	author = db.StringProperty(multiline=False)
	#when launching, remove "content" parameter
	content = db.StringProperty(multiline=True)
	avatar = db.BlobProperty()
	tag = db.StringProperty(multiline=False)
	date = db.DateTimeProperty(auto_now_add=True)
	#modify = db.DateTimeProperty()

class Tweet(db.Model):
	content = db.StringProperty(multiline=False)
	author = db.StringProperty(multiline=False)
	date = db.DateTimeProperty(auto_now_add=True)
	img = db.StringProperty(multiline=False)

class Room(db.Model):
	isPass = db.BooleanProperty(default=True)
	password = db.StringProperty(multiline=False)

class LoginPage(webapp.RequestHandler):
	def get(self):
		#session.delete()
		session["name"] = "no name"
		session["pass"] = "no pass"
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		template_value = {}
		self.response.out.write(template.render(path, template_value))

class Phrase(webapp.RequestHandler):
	def post(self):
		if len(self.request.get("tag")) > 0:
			session["tag"] = self.request.get("tag")
			session["name"] = self.request.get("name")
		room = Room.get_or_insert(session["tag"])
		room.put()
		self.redirect('/main')

class Check(webapp.RequestHandler):
	def post(self):
		session["pass"] = self.request.get("pass")
		self.redirect('/main')

class MainPage(webapp.RequestHandler):
	def get(self):
		if 'tag' in session:
			pass
		else:
			self.response.out.write("<font color='ff0000'> Enter Any Tag. </font>")
			self.redirect("/")

		room = Room.get_by_key_name(session["tag"])
		if room.isPass == False  and  session["pass"] != room.password:
				self.response.out.write("""Password: <form action='/check' method='post'><textarea name='pass' rows='1' cols='10'></textarea><input type='submit' value='submit'></form>""")

		else:
			isPass = room.isPass
			greetings = Greeting.gql("WHERE tag = :1 ORDER BY date DESC", session["tag"])

			tweets_list = []
			for greeting in greetings:
				temps = Tweet.gql("WHERE img = :1 ORDER BY date ASC", str(greeting.key()))
				tweets_list.append(temps)

			lists = zip(greetings, tweets_list)

			names = set([])
			for greeting in greetings:
				names |= set([greeting.author])
			members = list(names)
			members.sort()

			template_value = {
				'tag': session["tag"],
				'name': session["name"],
				'members': members,
				'lists': lists,
				'isPass': isPass,
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
		greeting = Greeting()
		#bug.... sometime missing tag and name.  why?
		greeting.tag = session["tag"]
		greeting.author = session["name"]
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
		tweet.author = session["name"]
		tweet.put()

		self.redirect('/main')

class Change(webapp.RequestHandler):
	def post(self):
		greetings = Greeting.gql("WHERE tag = :1", tag)
		for greeting in greetings:
			greeting.tag = self.request.get("newtag")
			greeting.put()
		session["tag"] = self.request.get("newtag")
		self.redirect('/main')

class Comment(webapp.RequestHandler):
	def post(self):
		tweet = Tweet()
		tweet.img = str(self.request.get("key"))
		tweet.content = self.request.get("comment")
		tweet.author = session["name"]
		tweet.put()
		self.redirect('/main')

class Forgot(webapp.RequestHandler):
	def post(self):
		greetings = Greeting.gql("WHERE author = :1", self.request.get("name"))
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
			'lists': lists,
			}
		path = os.path.join(os.path.dirname(__file__), 'forgot.html')
		self.response.out.write(template.render(path, template_value))

class Pass(webapp.RequestHandler):
	def post(self):
		room = Room.get_or_insert(session["tag"])
		room.isPass = not room.isPass
		if not room.isPass:
			room.password = self.request.get("pass")
			session["pass"] = room.password
		room.put()
		self.redirect('/main')

class Order(webapp.RequestHandler):
	def post(self):
		self.redirect('/main')

class Rmimg(webapp.RequestHandler):
	def post(self):
		greeting = db.get(self.request.get("key"))
		tweets = Tweet.gql("WHERE img = :1 ", str(self.request.get("key")))
		db.delete(greeting)
		db.delete(tweets)
		self.redirect('/main')

application = webapp.WSGIApplication([
		('/', LoginPage),
		('/main', MainPage),
		('/img', Image),
		('/sign', Guestbook),
		('/phrase', Phrase),
		('/change', Change),
		('/comment', Comment),
		('/forgot', Forgot),
		('/pass', Pass),
		('/order', Order),
		('/rmimg', Rmimg),
		('/check', Check)
		], debug=True)

def main():
	run_wsgi_app(application)

if __name__ == '__main__':
	main()
