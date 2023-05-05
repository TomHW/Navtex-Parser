'''
Navtex.parse -- Parse position data from NAVTEX messages

Navtex.parse is a program to read text messages from NAVTEX receiver.

It defines classes_and_methods

@author:     Thomas Hoffmann

@copyright:  2023 TiBeTo. All rights reserved.

@license:    MIT License (MIT)

@contact:    tom@tibeto.de

@deffield    updated: Updated
'''

from datetime import datetime, timezone
from pathlib import Path
import re
import calendar
import locale
import requests
from bs4 import BeautifulSoup
import io

class MessageParser():
	
	
	def __init__(self, folders, verbose=False):
		self.folders = folders
		self.messageLists = {}
		self.verbose = verbose
		self.mon_to_num_en = {name.upper(): num for num, name in enumerate(calendar.month_abbr) if num}
		locale.setlocale(locale.LC_TIME, '')
		self.mon_to_num_de = {name.upper(): num for num, name in enumerate(calendar.month_abbr) if num}
		locale.resetlocale(locale.LC_TIME)

	
	def parseAll(self):
		for path in self.folders:
			of = 'default'
			for ppart in path.split('/'):
				if len(ppart) > 0:
					of = ppart 
			if m := re.match(r'^\s*https?://([^/]+)/.*', path):
				self.messageLists[of] = self.parse_html(path)
			else:
				self.messageLists[of] = self.iterate_directory(path)
				pass

	def parse_html(self, url):
		if m := re.match(r'.*\.dwd\..*', url):
			response = requests.get(url)
			if response.status_code < 400:
				feature_collection = {'type': 'FeatureCollection', 'features': []}
				content = response.content
				bs = BeautifulSoup(content, "html.parser")
				msgs = bs.body.find('pre').text
#				print(msgs)
				msgs_lines = msgs.split('\n')
				in_msg = False
				msgLines = []
				for line in msgs_lines:
					if in_msg and re.match(r'^\s*NNNN\s*', line):
						if self.verbose:
							print('Message End')
						msgLines.append(line.strip())
						feature = self.parse_io_message(msgLines)
						if feature:
							feature_collection['features'].append(feature)
						msgLines = []
						in_msg = False
					elif re.match(r'^\s*ZCZC\s.*', line):
						if self.verbose:
							print('Message Start: ' + line)
						msgLines.append(line.strip())
						in_msg = True
					elif in_msg:
						msgLines.append(line.strip())
				return feature_collection
			else:
				return {'Error': response.status_code }
						
	
	def iterate_directory(self, dir_path):
		pathlist = Path(dir_path + '/').rglob('*.TXT')
		feature_collection = {'type': 'FeatureCollection', 'features': []}
		for path in pathlist:
			# because path is object not string
			path_str = str(path)
			if self.verbose:
				print(path)
			with open(path_str, "r") as msgfile:
				msgLines = [line.strip() for line in msgfile]
			feature = self.parse_io_message(msgLines)
			if feature:
				feature_collection['features'].append(feature)
		return feature_collection
			
	def parse_io_message(self, lines):
		if self.verbose:
			print(f"parse_io_message with {len(lines)} lines")
		call_sign = None
		station = None
		msgtype = None
		msg_no = -1
		msg_date = datetime.now()
		msg_text = ''
		positions = []
		feature = None
		has_area = False
		has_track = False
		for line in lines:
			msg_text += line + '\n'
			if m := re.match(r'^.*ZCZC\s+(\w)(\w)(\d\d)', line):
				station = m.group(1)
				msgtype = m.group(2)
				msg_no = m.group(3)
				call_sign = station + msgtype + msg_no
				if self.verbose:
					print(f"Call Sign: {call_sign}, Station: {station}, Type: {msgtype}, No: {msg_no}")
			elif m := re.match(r'^.*\bAREA\b.*', line, ):
				has_area = True
			elif m := re.match(r'^.*\bTRACK\b.*', line, ):
				has_track = True
			elif m := re.match(r'^\s*(\d\d)(\d\d)(\d\d)\s+UTC\s+([A-Z]{3})(?:\s+(\d\d))?.*', line):
				day = int(m.group(1))
				hour = int(m.group(2))
				minute = int(m.group(3))
				if m.group(4) in self.mon_to_num_en:
					month = self.mon_to_num_en[m.group(4)] 
				elif m.group(4) in self.mon_to_num_de:
					month = self.mon_to_num_de[m.group(4)]
				else:
					print(f"Call sign {call_sign} has unknown locale for month: {m.group(4)}")
					month = msg_date.month
				if m.group(5):
					year = int(m.group(5)) + 2000
				else:
					year = msg_date.year
				msg_date = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
			elif mi := re.finditer(r'\s*(\d\d)[\s!-](\d\d(?:[\.,]\d+)?)\s*([NS])[\s_-]+(\d{3})[\s!-](\d\d(?:[\.,]\d+)?)\s*([EW])\s*', line):
				for m in mi: 
					platdeg = m.group(1)
					platmin = m.group(2).replace(',', '.')
					platdir = m.group(3)
					plondeg = m.group(4)
					plonmin = m.group(5).replace(',', '.')
					plondir = m.group(6)
					if self.verbose:
						print(m.group(0))
					lat = self.degmin2float(platdeg, platmin, platdir)
					lon = self.degmin2float(plondeg, plonmin, plondir)
					positions.append([lon, lat])
					if self.verbose:
						print(f"https://map.openseamap.org/?zoom=10&lon={lon}&lat={lat}&layers=TFTFFFTFFTFFFFFFTFFFFF&mlat={lat}&mlon={lon}&mtext={call_sign}")
		if len(positions) > 0:
			feature = {'type': 'Feature',
					'id': call_sign,
					'properties': {
						'call-sign': call_sign,
						'station': station,
						'msg-type': msgtype,
						'msg-no': msg_no,
						'msg-date': msg_date.astimezone().isoformat(),
						'message': msg_text
					}
			}
		if (len(positions) == 1):
			feature['geometry'] = {'type': 'Point', 'coordinates': positions[0]}
		elif (len(positions) == 2):
			feature['geometry'] = {'type': 'MultiPoint', 'coordinates': positions}
		elif (len(positions) > 2):
			if has_area:
				positions.append(positions[0])		# close polygon
				feature['geometry'] = {'type': 'Polygon', 'coordinates': [ positions ]}
			elif has_track:
				feature['geometry'] = {'type': 'LineString', 'coordinates': positions }
			else:
				feature['geometry'] = {'type': 'MultiPoint', 'coordinates': positions}
		return feature
	
	
	def degmin2float(self, deg, minute, quarter):
		res = float(deg) + float(minute) / 60
		if(quarter == 'N' or quarter == 'E'):
			return res
		else:
			return -res
