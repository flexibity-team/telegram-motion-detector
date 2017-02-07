http://www.pyimagesearch.com/2015/10/26/how-to-install-opencv-3-on-raspbian-jessie/

installing python + OpenCV

sudo apt-get update
sudo apt-get upgrade

Устаналиваем необходимые пакеты для сборки OpenCV

sudo apt-get install -y build-essential git cmake pkg-config libjpeg8-dev libtiff5-dev libjasper-dev libpng12-dev libgtk2.0-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libatlas-base-dev gfortran

Step 7:

Install pip , a Python package manager:

wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py

Step 8:

Install virtualenv and virtualenvwrapper. These two packages allow us to create separate Python environments for each project we are working on. While installing virtualenv  and virtualenvwrapper  is not a requirement to get OpenCV 3.0 and Python 2.7+ up and running on your Ubuntu system, I highly recommend it and the rest of this tutorial will assume you have them installed!

sudo pip install virtualenv virtualenvwrapper
sudo rm -rf ~/.cache/pip

Now that we have virtualenv  and virtualenvwrapper  installed, we need to update our ~/.bashrc  file:

# virtualenv and virtualenvwrapper
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh

This quick update will ensure that both virtualenv  and virtualenvwrapper  are loaded each time you login.

To make the changes to our ~/.bashrc  file take effect, you can either (1) logout and log back in, (2) close your current terminal window and open a new one, or preferably, (3) reload the contents of your ~/.bashrc  file:

source ~/.bashrc

Lastly, we can create our cv  virtual environment where we’ll be doing our computer vision development and OpenCV 3.0 + Python 2.7+ installation:
mkvirtualenv cv

Step 9:

As I mentioned above, this tutorial covers how to install OpenCV 3.0 and Python 2.7+ (I’ll have a OpenCV 3.0 + Python 3 tutorial available later this month), so we’ll need to install our Python 2.7 development tools:

sudo apt-get install python2.7-dev

Since OpenCV represents images as multi-dimensional NumPy arrays, we better install NumPy into our cv  virtual environment:

pip install numpy

Our environment is now all setup — we can proceed to change to our home directory, pull down OpenCV from GitHub, and checkout the 3.1.0  version:

$ cd ~
$ git clone https://github.com/Itseez/opencv.git
$ cd opencv
$ git checkout 3.1.0

Update (3 January 2016): You can replace the 3.0.0  version with whatever the current release is (as of right now, it’s 3.1.0 ). Be sure to check OpenCV.org for information on the latest release.

As I mentioned last week, we also need the opencv_contrib repo as well. Without this repository, we won’t have access to standard keypoint detectors and local invariant descriptors (such as SIFT, SURF, etc.) that were available in the OpenCV 2.4.X version. We’ll also be missing out on some of the newer OpenCV 3.0 features like text detection in natural images:

cd ~
git clone https://github.com/Itseez/opencv_contrib.git
cd opencv_contrib
git checkout 3.1.0

Again, make sure that you checkout the same version for opencv_contrib  that you did for opencv  above, otherwise you could run into compilation errors.

Time to setup the build:

cd ~/opencv
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=RELEASE \
	-D CMAKE_INSTALL_PREFIX=/usr/local \
	-D INSTALL_C_EXAMPLES=ON \
	-D INSTALL_PYTHON_EXAMPLES=ON \
	-D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
	-D BUILD_EXAMPLES=ON ..

Update (3 January 2016): In order to build OpenCV 3.1.0 , you need to set -D INSTALL_C_EXAMPLES=OFF  (rather than ON ) in the cmake  command. There is a bug in the OpenCV v3.1.0 CMake build script that can cause errors if you leave this switch on. Once you set this switch to off, CMake should run without a problem.

Notice how compared to last week our CMake command is substantially less verbose and requires less manual tweaking — this is because CMake is able to better automatically tune our install parameters (at least compared to OSX).

Now we can finally compile OpenCV:

make -j4

Where you can replace the 4 with the number of available cores on your processor to speedup the compilation.

Here’s an example of OpenCV 3.0 compiling on my system:

Assuming that OpenCV compiled without error, you can now install it on your Ubuntu system:

sudo make
sudo checkinstall
sudo ldconfig

Step 11:

If you’ve reached this step without an error, OpenCV should now be installed in  /usr/local/lib/python2.7/site-packages

If you’ve reached this step without an error, OpenCV should now be installed in  /usr/local/lib/python2.7/site-packages

However, our cv  virtual environment is located in our home directory — thus to use OpenCV within our cv  environment, we first need to sym-link OpenCV into the site-packages  directory of the cv  virtual environment:

cd ~/.virtualenvs/cv/lib/python2.7/site-packages/
ln -s /usr/local/lib/python2.7/site-packages/cv2.so cv2.so

Step 12:

Congratulations! You have successfully installed OpenCV 3.0 with Python 2.7+ bindings on your Ubuntu system!

To confirm your installation, simply ensure that you are in the cv  virtual environment, followed by importing cv2 :

workon cv
python
import cv2
cv2.__version__
'3.0.0'

Here’s an example of demonstrating the OpenCV 3.0 and Python 2.7+ install on my own Ubuntu machine:

Step 13:

Now that OpenCV has been configured and installed, let’s build a quick Python script to detect the red game cartridge in the image named games.jpg  below:

Open up your favorite editor, create a new file, name it find_game.py , and insert the following code:

# import the necessary packages
import numpy as np
import cv2

# load the games image
image = cv2.imread("games.jpg")

# find the red color game in the image
upper = np.array([65, 65, 255])
lower = np.array([0, 0, 200])
mask = cv2.inRange(image, lower, upper)

# find contours in the masked image and keep the largest one
(_, cnts, _) = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
	cv2.CHAIN_APPROX_SIMPLE)
c = max(cnts, key=cv2.contourArea)

# approximate the contour
peri = cv2.arcLength(c, True)
approx = cv2.approxPolyDP(c, 0.05 * peri, True)

# draw a green bounding box surrounding the red game
cv2.drawContours(image, [approx], -1, (0, 255, 0), 4)
cv2.imshow("Image", image)
cv2.waitKey(0)

You’ll also need to download the games.jpg image and place it in the same directory as your find_game.py  file. Once the games.jpg  file has been downloaded, you can execute the script via:

$ python find_game.py

Assuming that you have downloaded the games.jpg  image and placed it in the same directory as our find_game.py  script, you should see the following output:

Notice how our script was able to successfully detect the red game cartridge in the right portion of the image, followed by drawing a green bounding box surrounding it.

Obviously this isn’t the most exciting example in the world — but it has demonstrated that we have OpenCV 3.0 with Python 2.7+ bindings up and running on our Ubuntu system!

Summary

To celebrate the OpenCV 3.0 release, I am working my way through OpenCV 3.0 and Python 2.7/Python 3.4 installation instructions on OSX, Ubuntu, and the Raspberry Pi.

Last week I covered how to install OpenCV 3.0 and Python 2.7+ on OSX.

And today we covered how to install OpenCV 3.0 with Python 2.7 bindings on Ubuntu. I have personally tested these instructions on my own Ubuntu 14.04 machine, but they should work on any Debian-based system.

Next week we’ll continue the install-fest and hop back to OSX — this time installing OpenCV 3.0 and Python 3!

This will be the first time we’ve used Python 3 on the PyImageSearch blog, so you won’t want to miss it!

And please consider subscribing to the PyImageSearch Newsletter by entering your email address in the form below. As we work through the OpenCV install-fest, I’ll be sending out updates as each new OpenCV 3.0 + Python install tutorial is released!
