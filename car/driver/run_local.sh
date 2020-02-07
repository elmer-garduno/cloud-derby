#!/bin/bash

#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

###############################################
# Control GoPiGo car by sending sensor messages 
# to the cloud and receiving driving commands
###############################################

set -u # This prevents running the script if any of the variables have not been set
set -e # Exit if error is detected during pipeline execution

source ../../setenv-global.sh

export GOOGLE_APPLICATION_CREDENTIALS="$SERVICE_ACCOUNT_SECRET"

# This is subscription for the car to listen to incoming control messages
export COMMAND_SUBSCRIPTION="driving-command-subscription-$CAR_ID"

### Obstacle avoidance - the number of millimeters to stop the car before hitting an object
export BARRIER_DAMPENING="180"

### Car Camera position; UPSIDE DOWN=0; NORMAL=1 - this takes effect on the car as the image will be flipped before being sent to the cloud
export CAR_CAMERA_NORMAL="0"

### What color ball this car will be playing (default value)
export CAR_COLOR="red"

###############################################
# This is run once after creating new environment
###############################################
install() {
    echo_my "Installing Python, Pip and other libraries..."
    sudo apt-get install python
    sudo apt-get install python-pip
    sudo pip install --upgrade pip
    sudo pip install --upgrade google-cloud --ignore-installed six
    sudo pip install paho-mqtt
    sudo pip install --upgrade pip setuptools
    sudo pip install curtsies
    wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo python
    sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
    sudo pip install pyasn1 pyasn1-modules -U
    sudo pip install cryptography
    sudo pip install PyJWT 
    sudo pip install Pillow 
    wget https://pypi.python.org/packages/16/d8/bc6316cf98419719bd59c91742194c111b6f2e85abac88e496adefaf7afe/six-1.11.0.tar.gz#md5=d12789f9baf7e9fb2524c0c64f1773f8
    sudo tar -zxvf six-1.11.0.tar.gz
    sudo python ./six-1.11.0/setup.py install
}

###############################################
# One time car setup tasks
###############################################
setup() {
    echo_my "Setting up car environment for the first run..."
    if which pip; then
      echo "Python and Pip are already installed, skipping this step."
    else
      install
    fi

    wget https://pki.google.com/roots.pem
}

###############################################
# MAIN
###############################################
mkdir -p tmp
echo_my "CAR_ID=$CAR_ID"
INSTALL_FLAG=tmp/install.marker  # Location where the install flag is set to avoid repeated installs

cd py

# Start the car
if [[ $# -gt 0 && "$1" != ""  && "$1" == "--non-interactive" ]] ; then
  ./drive_local.py $PROJECT $COMMAND_SUBSCRIPTION --non-interactive
else
  ./drive_local.py $PROJECT $COMMAND_SUBSCRIPTION --model-file $1 --labels $2 --threshold $3
fi
