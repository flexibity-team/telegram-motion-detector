# USAGE
# python pi_surveillance.py --conf conf.json

# import the necessary packages
from pyimagesearch.tempimage import TempImage
#from picamera.array import PiRGBArray
#from picamera import PiCamera
import argparse
import warnings
import datetime
import json
import time
import cv2

from signal import signal, SIGINT, SIGTERM, SIGABRT

#telegram
from telegram.error import NetworkError, Unauthorized
from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=False, default='conf.json',
	help="path to the JSON configuration file")
args = vars(ap.parse_args())

# filter warnings, load the configuration and initialize Telegram
# client
warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

frame = None

def start(bot, u):
	global chatId
	chatId = u.message.chat_id
	bot.sendMessage(chat_id=chatId, text="Starting motion detector")
	
def stop(bot, u):
	global chatId
	bot.sendMessage(chat_id=u.message.chat_id, text="Stoppint detection")
	chatId = None
	
def frame(bot, u):
	#TODO: lock (and double buffer?) frame to keep motion region markup and OSD!
	global frame
	bot.sendMessage(chat_id=u.message.chat_id, text="Sending current frame")
	sendFrame(frame, u.message.chat_id)

def status(bot, u):	
	global chatId
	if (chatId is None):
		bot.sendMessage(chat_id=u.message.chat_id, text="Motion notifications not enabled")
	else:
		bot.sendMessage(chat_id=u.message.chat_id, text="Sending Motion notifications to " + `chatId`)
		
def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

if conf["use_telegram"]:
	logger.info( "Initing telegram API..." )
	updater = Updater(token=conf["telegram_token"])
	
	dp = updater.dispatcher
	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(CommandHandler('stop', stop))
	dp.add_handler(CommandHandler('status', status))
	dp.add_handler(CommandHandler('frame', frame))
	dp.add_error_handler(error)

	bot = updater.bot
	
	chatId = None
	updater.start_polling()
	logger.info( "Telegram Bot API inited" )

def sendFrame(frame, chatId):
	try:
		if chatId != None:
			logger.info("sending image")
			t = TempImage()
			cv2.imwrite(t.path, frame)
			bot.sendPhoto(chat_id=chatId, photo=open(t.path, 'rb'))
			t.cleanup()
	except NetworkError:
		logger.error("network error")
		sleep(1)
	except Unauthorized:
		# The user has removed or blocked the bot.
		logger.error( "Unauth" )
	except:
		logger.error( "Unknown" )

runMotionDet = True

def MoDetWork():
	global frame
	cap = cv2.VideoCapture(0)

	# allow the camera to warmup, then initialize the average frame, last
	# uploaded timestamp, and frame motion counter
	logger.info("[INFO] warming up...")
	time.sleep(conf["camera_warmup_time"])
	avg = None
	lastTelegramUpdate = datetime.datetime.now()
	motionCounter = 0
	# capture frames from the camera
	#for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=False):
	while(runMotionDet):
		timestamp = datetime.datetime.now()
		
		# grab the raw NumPy array representing the image and initialize
		# the timestamp and occupied/unoccupied text
		#frame = f.array
		# Capture frame-by-frame
		ret, frame = cap.read()
		
		text = "Unoccupied"

		# resize the frame, convert it to grayscale, and blur it
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		gray = cv2.GaussianBlur(gray, (21, 21), 0)

		# if the average frame is None, initialize it
		if avg is None:
			print "[INFO] starting background model..."
			avg = gray.copy().astype("float")
			#rawCapture.truncate(0)
			continue

		# accumulate the weighted average between the current frame and
		# previous frames, then compute the difference between the current
		# frame and running average
		cv2.accumulateWeighted(gray, avg, 0.5)
		frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

		# threshold the delta image, dilate the thresholded image to fill
		# in holes, then find contours on thresholded image
		thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255,
			cv2.THRESH_BINARY)[1]
		thresh = cv2.dilate(thresh, None, iterations=2)
		(_, cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)

		# loop over the contours
		for c in cnts:
			# if the contour is too small, ignore it
			if cv2.contourArea(c) < conf["min_area"]:
				continue

			# compute the bounding box for the contour, draw it on the frame,
			# and update the text
			(x, y, w, h) = cv2.boundingRect(c)
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
			text = "Occupied"

		# draw the text and timestamp on the frame
		ts = timestamp.strftime("%H:%m:%S-%d.%m.%Y")
		cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
			cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
		cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
			0.35, (0, 0, 255), 1)

		# check to see if the room is occupied
		if text == "Occupied":
			
			# increment the motion counter
			motionCounter += 1
			
			# check to see if the number of frames with consistent motion is
			# high enough
			if motionCounter >= conf["min_motion_frames"]:
				# check to see if enough time has passed between uploads
				logger.info("Motion")
				
				if conf["save_images"]:
					print "[SAVE] {}".format(ts)
					path = "{base_path}/{timestamp}.jpg".format(
						base_path=conf["save_base_path"], timestamp=ts)
						
					cv2.imwrite(path, frame)
					
				if conf["use_telegram"]:	
					sendFrame(frame, chatId) #TODO: use job queue
					
				#TODO: write video footage for motion episode!

				# reset the motion counter
				motionCounter = 0

		# otherwise, the room is not occupied
		else:
			motionCounter = 0

		# check to see if the frames should be displayed to screen
		if conf["show_video"]:
			# display the security feed
			cv2.imshow("Security Feed", frame)
			key = cv2.waitKey(1) & 0xFF

			# if the `q` key is pressed, break from the loop
			if key == ord("q"):
				break

		# clear the stream in preparation for the next frame
		# rawCapture.truncate(0)

def stopTelegram():
	if conf["use_telegram"]:
		logger.info( "stopping telegram" )
		updater.stop()

def signal_handler(signum, frame):
	logger.warn("Abortint")
	global runMotionDet
	runMotionDet = False
	
stop_signals=(SIGINT, SIGTERM, SIGABRT)
for sig in stop_signals:
	signal(sig, signal_handler)

MoDetWork()

stopTelegram()
