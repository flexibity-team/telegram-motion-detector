import json
import hashlib
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
        self.passwordHash = conf["password_hash"]

        dp = self.u.dispatcher

    	dp.add_handler(CommandHandler('start', self.startCmd))
    	dp.add_handler(CommandHandler('stop', self.stopCmd))
    	dp.add_handler(CommandHandler('status', self.statusCmd))
    	dp.add_handler(CommandHandler('frame', self.frameCmd))
        dp.add_handler(CommandHandler('deauth', self.deauthCmd))
    	dp.add_error_handler(self.error)

    	self.chatId = None
        self.started = False
    	self.u.start_polling()
    	self.logger.info( "Telegram Bot API started" )
        self.sendSingleFrame = False

    def startCmd(self, bot, u):
        if self.chatId == None:
            chat_id = u.message.chat_id
            arglist = u.message.text.split(" ", 2)
            if (len(arglist) > 1):
                m = hashlib.md5()
                m.update(arglist[1])

                #self.logger.info("Authorization attempt: " + m.hexdigest() + ":" + self.passwordHash)

                if(m.hexdigest() == self.passwordHash):
                    self.chatId = chat_id
                    self.started = True
                    self.bot.sendMessage(chat_id=self.chatId, text="Starting motion detector")
                else:
                    self.bot.sendMessage(chat_id=chat_id, text="Password doesn't match ")
            else:
                self.bot.sendMessage(chat_id=chat_id, text="Use /start <password> to start motion detector feed to this channel")
        else:
            if self.checkAuth(u):
                self.bot.sendMessage(chat_id=self.chatId, text="Starting motion detector")
                self.started = True

    def checkAuth(self, u):
        if self.chatId != None and u.message.chat_id == self.chatId:
            return True
        else:
            self.bot.sendMessage(chat_id=u.message.chat_id, text="Unauthorized!")

    def deauthCmd(self, bot, u):
        if self.checkAuth(u):
            self.bot.sendMessage(chat_id=self.chatId, text="Deauthorizing bot...")
            self.started = False
            self.chatId = None

    def stopCmd(self, bot, u):
        if self.checkAuth(u):
            self.bot.sendMessage(chat_id=self.chatId, text="Stopping detection")
            self.started = False

    def frameCmd(self, bot, u):
        if self.checkAuth(u):
            self.bot.sendMessage(chat_id=self.chatId, text="Sending current frame")
            self.sendSingleFrame = True

    def statusCmd(self, bot, u):
        if self.checkAuth(u):
            if (self.started == False):
                self.bot.sendMessage(chat_id=self.chatId, text="Motion notifications not enabled")
            else:
                self.bot.sendMessage(chat_id=self.chatId, text="Sending Motion notifications to " + `self.chatId`)

    def error(self, bot, update, error):
        self.logger.warn('Update "%s" caused error "%s"' % (update, error))

    def sendFrame(self, frame):
        chat_id = self.chatId
    	try:
            if chat_id != None and (self.started or self.sendSingleFrame):
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
            self.started = False
            self.logger.error( "Unauth. User has removed bot" )
    	except:
    		self.logger.error( "Unknown" )

        self.sendSingleFrame = False

    def stop(self):
       self.logger.info( "stopping telegram" )
       self.u.stop()
