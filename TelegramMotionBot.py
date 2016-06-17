import json
#telegram
from telegram.error import NetworkError, Unauthorized
from telegram.ext import Updater
from telegram.ext import CommandHandler

from pyimagesearch.tempimage import TempImage

import traceback
import logging

import cv2

from time import sleep

class Bot(object):

    def __init__(self, conf = {} ):
        self.logger = logging.getLogger(__name__)

        self.logger.info( "Initing telegram API..." )
        self.u = Updater(token=conf["token"])
        self.bot = self.u.bot

        dp = self.u.dispatcher

    	dp.add_handler(CommandHandler('start', self.startCmd))
    	dp.add_handler(CommandHandler('stop', self.stopCmd))
    	dp.add_handler(CommandHandler('status', self.statusCmd))
    	dp.add_handler(CommandHandler('frame', self.frameCmd))
    	dp.add_error_handler(self.error)

    	self.chatId = None
    	self.u.start_polling()
    	self.logger.info( "Telegram Bot API started" )
        self.sendSingleFrame = False

    def startCmd(self, bot, u):
    	self.chatId = u.message.chat_id
    	self.bot.sendMessage(chat_id=self.chatId, text="Starting motion detector") #TODO: add authorization phase

    def stopCmd(self, bot, u):
    	self.bot.sendMessage(chat_id=u.message.chat_id, text="Stopping detection")
    	self.chatId = None

    def frameCmd(self, bot, u):
    	self.bot.sendMessage(chat_id=u.message.chat_id, text="Sending current frame")
    	self.sendSingleFrame = True

    def statusCmd(self, bot, u):
    	if (self.chatId is None):
    		self.bot.sendMessage(chat_id=u.message.chat_id, text="Motion notifications not enabled")
    	else:
    		self.bot.sendMessage(chat_id=u.message.chat_id, text="Sending Motion notifications to " + `self.chatId`)

    def error(self, bot, update, error):
        self.logger.warn('Update "%s" caused error "%s"' % (update, error))

    def sendFrame(self, frame):
        chat_id = self.chatId
        self.sendSingleFrame = False
    	try:
    		if chat_id != None:
    			self.logger.debug("sending image")
    			t = TempImage()
    			cv2.imwrite(t.path, frame)
    			self.bot.sendPhoto(chat_id=chat_id, photo=open(t.path, 'rb'))
    			t.cleanup()
    	except NetworkError:
    		self.logger.error("network error")
    	except Unauthorized:
    		# The user has removed or blocked the bot.
    		self.chatId = None
    		self.logger.error( "Unauth. User has removed bot" )
    	except:
    		self.logger.error( "Unknown" )

    def stop(self):
       self.logger.info( "stopping telegram" )
       self.u.stop()
