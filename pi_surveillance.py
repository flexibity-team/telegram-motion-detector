# USAGE
# python pi_surveillance.py --conf conf.json

# import the necessary packages
from pyimagesearch.tempimage import TempImage

import argparse
import warnings
import datetime
import json
import time
from time import sleep
import cv2

from signal import signal, SIGINT, SIGTERM, SIGABRT

import logging

from TelegramMotionBot import Bot

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

bot = Bot(conf["telegram"])

runMotionDet = True

def MoDetWork():
	global frame
	cap = cv2.VideoCapture(0)

	# allow the camera to warmup, then initialize the average frame, last
	# uploaded timestamp, and frame motion counter
	logger.info("warming up...")
	time.sleep(conf["camera_warmup_time"])
	avg = None
	motionCounter = 0
	# capture frames from the camera
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
			logger.info( "starting background model..." )
			avg = gray.copy().astype("float")
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
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
			text = "Occupied"

		# draw the text and timestamp on the frame
		ts = timestamp.strftime("%Y.%m.%d-%H:%M:%S.%f")
		cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
			cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
		cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
			0.35, (0, 0, 255), 1)

		if bot.sendSingleFrame == True:
			bot.sendFrame(frame)

		# check to see if the room is occupied
		if text == "Occupied":

			# increment the motion counter
			motionCounter += 1

			# check to see if the number of frames with consistent motion is
			# high enough
			if motionCounter >= conf["min_motion_frames"]:
				# check to see if enough time has passed between uploads
				logger.debug("Motion")

				if conf["save_images"]:
					print "[SAVE] {}".format(ts)
					path = "{base_path}/{timestamp}.jpg".format(
						base_path=conf["save_base_path"], timestamp=ts)

					cv2.imwrite(path, frame)

				bot.sendFrame(frame)

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

def signal_handler(signum, frame):
	logger.warn("Aborting")
	global runMotionDet
	runMotionDet = False

stop_signals=(SIGINT, SIGTERM, SIGABRT)
for sig in stop_signals:
	signal(sig, signal_handler)

MoDetWork()

bot.stop()
