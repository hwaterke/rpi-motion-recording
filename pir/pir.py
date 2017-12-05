#!/usr/bin/env python2.7

import RPi.GPIO as GPIO
import MySQLdb
from datetime import datetime, date
import time
from threading import Event
import logging
import sys
GPIO.setmode(GPIO.BCM)
logging.basicConfig(filename='screen.log', level=logging.WARNING, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

#========================================
class MotionStorage:
  NAME = 'RaspberryPi'
  DB_IP = '192.168.xx.xx'
  DB_USER = 'xxxx'
  DB_PWD = 'xxxx'
  DB_NAME = 'xxxx'

  def open_connection(self):
    logging.info("Initializing database.")
    self.db = MySQLdb.connect(self.DB_IP, self.DB_USER, self.DB_PWD, self.DB_NAME)
    self.cursor = self.db.cursor()

  def close_connection(self):
    logging.info("Closing database.")
    self.db.close()

  def save_motion(self, event, value):
    query = "INSERT INTO motion(name, event, value, created_at, created_at_utc, updated_at) VALUES (%s, %s, %s, %s, %s, NOW())"
    values = (self.NAME, event, value, datetime.now(), datetime.utcnow())
    logging.debug("Saving to database: %s" % (values,))
    try:
      self.open_connection()
      self.cursor.execute(query, values)
      self.db.commit()
      self.close_connection()
    except Exception:
      logging.exception("Unable to commit to database")
      logging.error("Unable to save %s" % (values,))


#========================================
class Main:
  PIR_PIN = 4
  SLEEP_TIME = 60 * 5
  DB_MIN_INACTIVITY = 60 * 10

  def __init__(self):
    logging.info("PIR (CTRL+C to exit).")
    GPIO.setup(self.PIR_PIN, GPIO.IN)
    self.store = MotionStorage()
    self.last_motion = time.time()
    self.inactivity_logged = False
    self.motion_event = Event()
    logging.info("Ready.")

  def time_since_last_motion(self):
    return time.time() - self.last_motion

  def motion_callback(self, pin):
    # Let the main thread know that motion was detected.
    self.motion_event.set()

  def motion_detected(self):
    logging.debug("Motion detected.")
    time_since_last_motion = self.time_since_last_motion()
    # Save motion in DB
    if time_since_last_motion > self.DB_MIN_INACTIVITY:
      self.store.save_motion("MOTION_AFTER_INACTIVITY_OF", time_since_last_motion)
    self.inactivity_logged = False
    self.last_motion = time.time()

  def inactivity_detected(self):
    logging.debug("Inactivity detected.")
    time_since_last_motion = self.time_since_last_motion()
    # Save inactivity in DB
    if time_since_last_motion > self.DB_MIN_INACTIVITY and not self.inactivity_logged:
      self.store.save_motion("NO_MOTION_FOR", time_since_last_motion)
      self.inactivity_logged = True

  def start(self):
    try:
      GPIO.add_event_detect(self.PIR_PIN, GPIO.RISING, callback=self.motion_callback)
      while True:
        motion_detected = self.motion_event.wait(self.SLEEP_TIME)
        if motion_detected:
          self.motion_detected()
          self.motion_event.clear()
        else:
          self.inactivity_detected()
    except KeyboardInterrupt:
      logging.warn("Interrupt Ctrl-C")
    finally:
      logging.warn("Cleaning up")
      GPIO.cleanup()
#========================================
Main().start()
