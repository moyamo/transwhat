__author__ = "Steffen Vogel"
__copyright__ = "Copyright 2013, Steffen Vogel"
__license__ = "GPLv3"
__maintainer__ = "Steffen Vogel"
__email__ = "post@steffenvogel.de"
__status__ = "Prototype"

"""
 This file is part of transWhat

 transWhat is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 any later version.

 transwhat is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with transWhat. If not, see <http://www.gnu.org/licenses/>.
"""

import threading
import inspect
import re
import urllib
import time
import os
import utils

from constants import *

class Bot():
	def __init__(self, session, name = "Bot"):
		self.session = session
		self.name = name

		self.commands = {
			"help": self._help,
			"prune": self._prune,
			"welcome": self._welcome,
			"fortune": self._fortune,
			"sync": self._sync
		}

	def parse(self, message):
		args = message.split(" ")
		cmd = args.pop(0)

		if cmd[0] == '\\':
			try:
				self.call(cmd[1:], args)
			except KeyError:
				self.send("invalid command")
			except TypeError:
				self.send("invalid syntax")
		else:
			self.send("a valid command starts with a backslash")

	def call(self, cmd, args = []):
		func = self.commands[cmd]
		spec = inspect.getargspec(func)
		maxs = len(spec.args) - 1
		reqs = maxs - len(spec.defaults or [])
		if reqs > len(args) > maxs:
			raise TypeError()

		thread = threading.Thread(target=func, args=tuple(args))
		thread.start()

	def send(self, message):
		self.session.backend.handleMessage(self.session.user, self.name, message)

	def __get_token(self, filename, timeout = 30):
		file = open(filename, 'r')
		file.seek(-1, 2) # look at the end

		count = 0
		while count < timeout:
			line = file.readline()

			if line in ["", "\n"]:
				time.sleep(1)
				count += 1
				continue
			else:
				timestamp, number, token = line[:-1].split("\t")
				if (number == self.session.legacyName):
					file.close()
					return token

		file.close()

	# commands
	def _sync(self):
		user = self.session.legacyName
		password = self.session.password

		count = self.session.buddies.sync(user, password)
		self.session.updateRoster()

		if count:
			self.send("sync complete, %d buddies are using WhatsApp" % count)
		else:
			self.send("sync failed, sorry something went wrong")

	def _help(self):
		self.send("""following bot commands are available:
\\help				show this message
\\prune			clear your buddylist
\\sync			sync your imported contacts with WhatsApp
\\fortune [database]		give me a quote

following user commands are available:
\\lastseen			request last online timestamp from buddy""")

	def _fortune(self, database = '', prefix=''):
		if os.path.exists("/usr/share/games/fortunes/%s" % database):
			fortune = os.popen('/usr/games/fortune %s' % database).read()
			self.send(prefix + fortune[:-1])
		else:
			self.send("invalid database")

	def _welcome(self):
		motd = open(MOTD_FILE, "r").read()
		self.send(motd[:-1])
		self.call("fortune", ("disclaimer", "Disclaimer: "))

	def _prune(self):
		self.session.buddies.prune()
		self.session.updateRoster()
		self.send("buddy list cleared")
