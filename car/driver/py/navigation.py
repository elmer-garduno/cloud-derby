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

import math
import random
import time

import drive_message
import settings

# Highest allowed Y coordinate of the top of the ball in the picture - if it is above this, we will discard the image
# as false positive for low confidence result because balls should not fly in the air. Note that the coordinates of
# (0,0) are in the top left corner.
HIGH_BALL_TOP_BOUND = 0.1;

# Even if the ball is very high and if the inference confidence score is higher than this, we will still accept this
# as a real ball
HIGH_BALL_SCORE = 0.95;

# Ignore all Home Base objects if confidence score is lower than this below
HOME_BASE_SCORE = 0.3;

ANGLE_CALIBRATION_MULTIPLIER = 0.75

TURN_SPEED = settings.MAX_SPEED / 10
# Many GoPiGo motors are driving at different speed causing left and right motor to skew the car when driven at max,
# hence we reduce the max speed
DRIVE_SPEED = settings.MAX_SPEED / 3

def find_nearest_object(label, bounding_boxes, labels):
  """Based on the list of object locations, find the object closest to observer.
   This assumes that all objects of this label are the same size
   Input:
   - object label
   - list of object bounding boxes found by Object Detection
   Output:
   - Bounding box for the nearest object (may be undefined if object not found)
  """
  nearest_object = None
  found_size = 0
  for box in bounding_boxes:
    if labels.get(box.id, box.id) == label:
      # For object type of "ball" its upper border should never be 
      # above certain height of the image with low confidence score.
      if (label.endswith("Ball") and
          box.score < HIGH_BALL_SCORE and
          box.bbox.ymin < HIGH_BALL_TOP_BOUND):
        continue
      
      # Consider the largest size - vertical or horizontal (object may be covered partially) - and multiply this by
      # the confidence score
      size = max(box.bbox.xmax - box.bbox.xmin, box.bbox.ymax - box.bbox.ymin) * box.score
      # Is current object bigger and more likely than the one found earlier?
      if found_size < size:
        found_size = size
        nearest_object = box
  return nearest_object      


def find_nearest_color(bounding_boxes, labels):
  """Based on the list of object locations, find the object closest to observer.
   This assumes that all objects of this label are the same size
   Input:
   - object label
   - list of object bounding boxes found by Object Detection
   Output:
   - Bounding box for the nearest object (may be undefined if object not found)
  """
  nearest_color = None
  found_size = 0
  for box in bounding_boxes:
    current_label = labels.get(box.id, box.id)
    # For object type of "ball" its upper border should never be
    # above certain height of the image with low confidence score.
    if (current_label.endswith("Ball") and
        box.score < HIGH_BALL_SCORE and
        box.bbox.ymin < HIGH_BALL_TOP_BOUND):
      continue

    # Consider the largest size - vertical or horizontal (object may be covered partially) - and multiply this by
    # the confidence score
    size = max(box.bbox.xmax - box.bbox.xmin, box.bbox.ymax - box.bbox.ymin) * box.score
    # Is current object bigger and more likely than the one found earlier?
    if found_size < size:
      found_size = size
      nearest_color = current_label 
  return nearest_color

def find_angle(bounding_box):
  """Calculate the angle of the object off center of the image
   Input:
   - Coordinates of the object
   - Image metadata with info about the dimensions of the image
   Output:
   - Angle where the object is located - positive means turn right, negative is turn left
  """
    
  # Find horizontal center of the object
  center_x = bounding_box.xmin + (bounding_box.width / 2)
    
  # Find offset of the center of the object relative to the middle of the image
  # Negative offset means to the left, positive to the right
    
  # ------- This is if using pixels
  # Calculate angle of the object center relative to the image center
  # let offsetPixels = centerX - Settings.camera.HORIZONTAL_RESOLUTION_PIXELS / 2;
  # let angle = (settings.CAMERA_H_FIELD_OF_VIEW / 2) *
  #   (offsetPixels / (Settings.camera.HORIZONTAL_RESOLUTION_PIXELS / 2));
    
  # -------- This is using relative coordinates
  angle = (center_x - 0.5) * settings.CAMERA_H_FIELD_OF_VIEW * ANGLE_CALIBRATION_MULTIPLIER
    
  return round(angle);
      

def find_distance_mm(bounding_box, real_object_vertical_size_mm, 
                     real_object_horizontal_size_mm):
  """Calculate the distance to the object
   Input:
   - bounding box with the dimensions of the image
   - Vertical Object size
   Output:
   - Distance to the object in mm
  """
    
  # Use the largest dimension because objects can be partially visible - hence we calculate expected vs visible
  # size ratio of object
  expected_ratio = real_object_vertical_size_mm / real_object_horizontal_size_mm
  visible_ratio = bounding_box.height / bounding_box.width
  print("expected > visible: {} -> {} ".format(expected_ratio, visible_ratio))
    
  # Depending if we see more of a width vs height use that for calculations
  if expected_ratio < visible_ratio :
    sensor_size_mm = settings.CAMERA_SENSOR_HEIGHT_MM
    real_object_size_mm = real_object_vertical_size_mm
    relative_object_size = bounding_box.height
  else:
    sensor_size_mm = settings.CAMERA_SENSOR_WIDTH_MM
    real_object_size_mm = real_object_horizontal_size_mm
    relative_object_size = bounding_box.width

  distance_mm = ((settings.CAMERA_FOCAL_LENGTH_MM * real_object_size_mm) / 
      (relative_object_size * sensor_size_mm)) - settings.MIN_DISTANCE_TO_CAMERA_MM
 
  print("distance >> {}".format(distance_mm))
   
  if distance_mm < 115:
    distance_mm = 20
  elif distance_mm < 325:
    distance_mm = distance_mm - 35
  print("distance >> {}".format(distance_mm)) 
  return round(distance_mm);


def make_timestamp():
  return int(time.time() * 1000) 


def calculate_ball_directions(bounding_box):
  """Calculates sequence of directions to the specified ball as defined by the bounding box
   Input:
   - bBox - bounding box with coordinates of the nearest ball
   - obstacleFound - did we detect an obstacle
   Output:
   - Initialized command object with sequence of actions/directions
"""
  angle = find_angle(bounding_box)
  print(">>>>> angle {}".format(angle))
  distance = find_distance_mm(bounding_box, settings.BALL_SIZE_MM, settings.BALL_SIZE_MM)
  print(">>>>> distance {}".format(distance))

  # --- At this distance we can close gripper and have our ball
  BALL_CAPTURE_DISTANCE_MM = 45
  # Camera mounts used on cars in Europe
  # ball_capture_distance_mm = 70;
    
  # At this distance or closer we need to be moving slow not to kick the ball out too far
  SLOW_APPROACH_ZONE_MM = 300
  # We can grasp the ball within this angle spread to each side
  BALL_CAPTURE_ANGLE = 11
  # This is how far the car will drive super slowly to make sure ball is really in the gripper
  EXTRA_DISTANCE = 40
  
  if abs(angle) <= BALL_CAPTURE_ANGLE and distance <= BALL_CAPTURE_DISTANCE_MM:
    command_queue = []
    # If we came here second time after gripping the ball, this means we really have it in the gripper and can now
    # go to the base
    # TODO(elmerg): Fix this part
    #    if (this.commandHistory[this.commandHistory.length - 1].goal == CHECK_GRIP) {
    #      command.setGoalGo2Base();
    #      return command;
    #    }
    # We are close enough and at the proper angle so that we can capture the ball (yay!)
    command_queue.append((make_timestamp(), "gripperPosition", "close"))
    # command.gripperClose();
    # We set the goal to check grip so that we come into this second time we know what we wanted to do - see code
    # above
    # ->>> command.setGoalCheck4Grip();
    # Drive backwards so we can make sure next time we still have the ball in the grip
    command_queue.append((make_timestamp(), "setSpeed", DRIVE_SPEED))
    # command.setSpeed(DRIVE_SPEED);
    command_queue.append(drive_message.drive(-BALL_CAPTURE_DISTANCE_MM * 3))
    # command.drive(-ballCaptureDistanceMm * 3)
    return command_queue
    
  # First part of the distance go at max speed
  speed = DRIVE_SPEED
  
  command_queue = []  
  if distance < SLOW_APPROACH_ZONE_MM:
    # ->>>> command.setGoalGo2Ball();
    # Turn slowly towards the ball to avoid jerking the car and kicking the ball
    command_queue.append((make_timestamp(), "setSpeed", settings.MAX_SPEED * 0.1))
    # command.setSpeed(Settings.MAX_SPEED * 0.1);
    command_queue.append(drive_message.make_turn(angle))
    # command.makeTurn(angle);
    command_queue.append((make_timestamp(), "gripperPosition", "open"))
    # command.gripperOpen();
    # Last part of the journey we need to slow down as to not kick the ball away
    speed = settings.MAX_SPEED * 0.05
    # Always drive extra few cm to make sure we have the ball in the gripper
    distance = distance + EXTRA_DISTANCE
    # TODO(elmerg): Fix this part
    # } else if (obstacleFound) {
    #  console.log("calculateBallDirections(): these aren't the droids you're looking for. Navigating around the obstacle...");
    #  return this.ballSearchStrategy();
  else:
    # ->>>> command.setGoalGo2Ball()
    command_queue.append(drive_message.make_turn(angle))
    # command.makeTurn(angle);
    distance = distance - SLOW_APPROACH_ZONE_MM * 0.5
    
  command_queue.append((make_timestamp(), "setSpeed", speed))
  # command.setSpeed(speed);
  command_queue.append(drive_message.drive(distance))
  # command.drive(distance);
  return command_queue

def navigate_to_ball(label, objects, labels):
  """Navigates to the closest ball of the given type."""
  if not objects:
    print('No objects of type {} detected'.format(label))
    return False, []
  else:
    #print("objects: {}".format(objects))
    nearest_color = find_nearest_color(objects, labels)
    set_color_command = (make_timestamp(), "setColor", nearest_color)
    object = find_nearest_object(label, objects, labels)
    
    if not object:
      print('No objects of type {} detected'.format(label))
      return False, [set_color_command]
    print(labels.get(object.id, object.id))
    print('  id:    ', object.id)
    print('  score: ', object.score)
    print('  bbox:  ', object.bbox)
   
    command_queue = calculate_ball_directions(object.bbox)
    # TODO(elmerg): Ignore bad messages, I need to fix the source of the meessages
    if command_queue:
      command_queue = [command for command in command_queue if command] 
      target_found = True 
    else:
      target_found = False
    return target_found, [set_color_command] + command_queue
 

def ball_search_strategy(ball_turns):
  """The required ball is not in the picture frame - need to
   formulate strategy to move the car to ball appears in the frame in the future
   Input:
   - list of object bounding boxes found by Object Detection
   Output:
   - Driving commands for car to execute in pursuit of search for the ball
  """
  command_queue = []
  if ball_turns < 5:
    angle = 67;
    # Try to put a ball in a picture frame
    # -->>>>command.setGoalSeekBallTurn();
    command_queue.append((make_timestamp(), "setSpeed", TURN_SPEED))
    # command.setSpeed(TURN_SPEED);
    command_queue.append(drive_message.make_turn(angle))
    # command.makeTurn(angle);
  else:
    # However if after several turns the ball was still not found, need to drive somewhere
    # to change car position and take new pictures from there
    # Try to put a ball in a picture frame
    # -->>>>command.setGoalSeekBallMove();
    min_distance_mm = 300
    max_random_distance_mm = 900
    distance = min_distance_mm + math.floor(random.random() * max_random_distance_mm);
    if random.random() < 0.20:
      # On random rare occasion drive backward
      distance = -distance
      
    # Since we do not need high precision - can turn very quickly here - may help to push things away
    command_queue.append((make_timestamp(), "setSpeed", settings.MAX_SPEED))
    #  command.setSpeed(Settings.MAX_SPEED)
    command_queue.append(drive_message.drive(distance))
    #  command.drive(distance)
  return command_queue
