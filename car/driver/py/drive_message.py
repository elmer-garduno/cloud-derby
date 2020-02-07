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

import time

# For some reason car gets stuck in limbo when the turn angle is 3 degrees or less
_IGNORE_TURN_DEGREE = 3


def _make_timestamp():
  return int(time.time() * 1000)


def drive_forward(mm):
  """Cap max driving distance in any conditions to no more than 5 meters."""
  if mm > 0:
    return (_make_timestamp(), "driveForwardMm", min(mm, 5000))


def drive_backward(mm):
  """Cap max driving distance in any conditions to no more than 5 meters."""
  if mm <= 0:
    return (_make_timestamp(), "driveBackwardMm", min(mm, 5000))


def drive(mm):
  # This takes positive or negative value and converts it into a proper command
  # If speed is not explicitly set in the command, then drive at max speed
  if mm > 0:
    return drive_forward(mm)
  else:
    return drive_backward(mm)


def turn_left(degrees):
  # Cap max turn angle to 1000 degrees in any conditions
  if degrees < 0 and abs(degrees) > _IGNORE_TURN_DEGREE:
    return (_make_timestamp(), "turnLeft", min(degrees, 1000))


def turn_right(degrees):
  # Cap max turn angle to 1000 degrees in any conditions
  if degrees > _IGNORE_TURN_DEGREE:
    return (_make_timestamp(), "turnRight", min(degrees, 1000))


def make_turn(degrees):
  # This takes positive or negative angle and converts it into a proper command  
  if degrees > 0:
    return turn_right(degrees)
  else:
    return turn_left(degrees)

