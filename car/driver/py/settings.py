# Copyright 2020 Google LLC
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

# Diameter of the ball
#BALL_SIZE_MM = 60.64
BALL_SIZE_MM = 44.64 
 
# Width of the Home Base sign (letter size is 216mm, but the letter is not printed on 100% of the paper)
HOME_WIDTH_MM = 200
  
# Height of the Home Base sign (letter size is 280mm, but the letter is not printed on 100% of the paper)
HOME_HEIGHT_MM = 250
  
# Distance from the camera to the ball in a fully captured position - this is defined by the location of the
# camera when it is mounted on the ball gripper
MIN_DISTANCE_TO_CAMERA_MM = 21
  
# Max car speed (wheel rotation degrees per second)
MAX_SPEED = 1000
  
# Here is the camera model used in the car:
# https://www.amazon.com/gp/product/B00RMV53Z2
    
# Horizontal field of view for the camera mounted on the car - degrees out of 360
CAMERA_H_FIELD_OF_VIEW = 120.0
    
# Size of the camera sensor is 1/4 inch - see more details: https://en.wikipedia.org/wiki/Image_sensor_format
CAMERA_SENSOR_HEIGHT_MM = 2.7
CAMERA_SENSOR_WIDTH_MM = 3.6
    
# Focal length of the camera - it is adjustable, so we need to calibrate it before using this camera for navigation
CAMERA_FOCAL_LENGTH_MM = 2.594
    
# Horizontal resolution
# HORIZONTAL_RESOLUTION_PIXELS: process.env.HORIZONTAL_RESOLUTION_PIXELS,
# VERTICAL_RESOLUTION_PIXELS: process.env.VERTICAL_RESOLUTION_PIXELS
