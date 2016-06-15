from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging

import signal
import sys

updater = Updater(token='224166329:AAG9wcyrLp0vrnYveM6q6Ipcg-dVcp4WvPY')

dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

botHandler = None

def start(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")
	botHandler = bot


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def signal_handler(signal, frame):
	print('You pressed Ctrl+C!')
	updater.stop()
	sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
print('Press Ctrl+C to exit')

updater.start_polling()

updater.idle()
