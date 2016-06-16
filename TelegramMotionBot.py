import json
#telegram
from telegram.error import NetworkError, Unauthorized
from telegram.ext import Updater
from telegram.ext import CommandHandler

import traceback
import logging

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

    def startCmd(self, bot, u):
        traceback.print_stack()
    	self.chatId = u.message.chat_id
    	self.bot.sendMessage(chat_id=self.chatId, text="Starting motion detector") #TODO: add authorization phase

    def stopCmd(self, bot, u):
    	self.bot.sendMessage(chat_id=u.message.chat_id, text="Stopping detection")
    	self.chatId = None

    def frameCmd(self, bot, u):
    	#TODO: lock (and double buffer?) frame to keep motion region markup and OSD!
    	self.bot.sendMessage(chat_id=u.message.chat_id, text="Sending current frame")
    	#sendFrame(frame, u.message.chat_id)

    def statusCmd(self, bot, u):
    	if (self.chatId is None):
    		self.bot.sendMessage(chat_id=u.message.chat_id, text="Motion notifications not enabled")
    	else:
    		self.bot.sendMessage(chat_id=u.message.chat_id, text="Sending Motion notifications to " + `self.chatId`)

    def error(self, bot, update, error):
        self.logger.warn('Update "%s" caused error "%s"' % (update, error))

    def sendFrame(self, frame, chat_id = None):
    	if chat_id is None:
    		chat_id = self.chatId

    	#self.lastTelegramUpdate = datetime.datetime.now()
    	try:
    		if chat_id != None:
    			self.logger.debug("sending image")
    			t = TempImage()
    			#cv2.imwrite(t.path, frame)
    			#bot.sendPhoto(chat_id=chat_id, photo=open(t.path, 'rb'))
    			#t.cleanup()
    	except NetworkError:
    		self.logger.error("network error")
    		sleep(1)
    	except Unauthorized:
    		# The user has removed or blocked the bot.
    		if chat_id is None: #it was global chatId (motion feed), reset it
    			chatId = None
    		self.logger.error( "Unauth. User has removed bot" )
    	except:
    		self.logger.error( "Unknown" )

    def stop(self):
       self.logger.info( "stopping telegram" )
       self.u.stop()
