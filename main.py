#!/usr/bin/python
#
# Copyright (C) Marcos Talau 2015
# Author Marcos Talau (talau@users.sourceforge.net)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import traceback
import sys

import requests
import base64
from BeautifulSoup import BeautifulSoup
import internet_util
import time
import config
import os

ip = config.router_ip
cookie_auth = None

def get_cookie_auth(user, password):
	cookie = dict(Authorization='Basic %s'% base64.b64encode("%s:%s" % (user,password)))
	printd("HTTP login in %s u=%s p=%s" % (ip, user, password))
	r = requests.get("http://%s"%ip, cookies=cookie)

	if r.text.find("loginBox") != -1:
		print("ERROR: user and/or password incorrect")
		sys.exit(1)
	# get cookie
	return dict(Authorization=r.cookies['Authorization'])

def get_wan_int_status():
	print cookie_auth
	r = requests.get("http://%s/info.html"%ip, headers={'Referer':'http://%s/'%ip}, cookies=cookie_auth)

	print r.text

def get_wan_info():
	p = {'action': 'view'}
	printd("HTTP WAN INFO")
	r = requests.get("http://%s/wancfg.cmd"%ip, params=p, headers={'Referer':'http://%s/'%ip}, cookies=cookie_auth)
	
	t = r.text.encode('utf-8')

	# TODO: get WAN int
	status = t.split("|PPPoE|")[1].split("|")[3]
	ip_wan = t.split("|PPPoE|")[1].split("|")[2]

	return [status, extract_sessionkey(r.text), ip_wan]

def extract_sessionkey(html):
	r = html.split("var sessionKey = ")
	key = r[1].split(";")[0]

	return key.replace("'", "")

def do_wan_action(action, sessionkey):
	if action == "up":
		manual = '1'
	else:
		manual = '0'

	# TODO: get the name of the interface
	p = {'action': 'manual', 'manual': manual, 'ifName': 'ppp0.1', 'sessionKey':sessionkey}

	printd("HTTP action %s" % action)
	r = requests.get("http://%s/wancfg.cmd"%ip, params=p, headers={'Referer':'http://%s/'%ip}, cookies=cookie_auth)

def log(status):
	t = time.strftime("%Y/%m/%d %H:%M")
	f = open(config.log_file, "a")
	f.write("%s %s\n" % (status, t))
	f.close()

def printd(s):
	if config.debug:
		print(s)
	
# main
action = config.action
user = config.router_user
password = config.router_pass

if internet_util.have_internet():
	if config.log_net_on:
		log("on")
	printd("net already on")
	if action == "up":
		printd("so, exiting")
		sys.exit(0)
else:
	if config.log_net_off:
		log("off")
	printd("net is off")

cookie_auth = get_cookie_auth(user, password)
printd("cookie %s" % cookie_auth)

i = get_wan_info()
status = i[0]
sessionkey = i[1]
printd("status of WAN %s" % status)
if action == "up":
	# do down when Connected because net is off at this point
	if status == "Connected":
		if config.log_false_connected:
			log("false connected")
		# try code here to http/html debug if fail occour in cron
		try:
			do_wan_action("down", sessionkey)
		except:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
			print ''.join('!! ' + line for line in lines)  
		time.sleep(4)
		i = get_wan_info()
		sessionkey = i[1]
	do_wan_action("up", sessionkey)
	if config.process_wan_ip:
		printd("Processing WAN IP")
		time.sleep(15)
		i = get_wan_info()
		printd("WAN IP address: %s" % i[2])
		if config.wan_ip_cmd != "":
			printd("Running command %s" % config.wan_ip_cmd)
			os.system("%s %s" % (config.wan_ip_cmd, i[2]))
else:
	do_wan_action("down", sessionkey)
