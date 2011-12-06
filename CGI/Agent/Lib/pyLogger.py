# -*- coding: utf-8 -*-
import logging
import logging.handlers

class pylogger:
	
	def __init__(self, logName, logFilename):
		# create logger
		self.Logger = logging.getLogger(logName)
		self.Logger.setLevel(logging.DEBUG)

		handler = logging.handlers.RotatingFileHandler(
              logFilename, maxBytes=2000, backupCount=5)
		
		handler.setLevel(logging.DEBUG)

		formatter = logging.Formatter("%(asctime)s-%(name)s-%(levelname)s\n-%(message)s")

		handler.setFormatter(formatter)

		self.Logger.addHandler(handler)
	
	def getLogger(self):
		return self.Logger
		
	def debug(self, msg):
		self.Logger.debug(msg)
	def info(self, msg):	
		self.Logger.info(msg)
	def warn(self, msg):	
		self.Logger.warn(msg)
	def error(self, msg):	
		self.Logger.error(msg)
	def critical(self, msg):	
		self.Logger.critical(msg)
		
# bart-> you python file name
# lg = pylogger('bart','/var/log/acl.log')	
# lg.debug("debug message")
# lg.info("info message")
# lg.warn("warn message")
# lg.error("error message")
# lg.critical("critical message")