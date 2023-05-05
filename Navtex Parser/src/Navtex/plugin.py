'''
Navtex.parse -- Parse position data from NAVTEX messages

Navtex.parse is a program to read text messages from NAVTEX receiver.

It defines classes_and_methods

Plugin template from Andreas Wellenvogel, adapted for Navtex requirements

@author:     Andreas Wellenvogel, Thomas Hoffmann 

@copyright:  2023 TiBeTo. All rights reserved.

@license:    MIT License (MIT)

@contact:    tom@tibeto.de

@deffield    updated: Updated
'''
#the following import is optional
#it only allows "intelligent" IDEs (like PyCharm) to support you in using it
import urllib.request
import os
import time
import json

class Plugin(object):

	@classmethod
	def pluginInfo(cls):
		"""
		the description for the module
		@return: a dict with the content described below
						parts:
							 * description (mandatory)
							 * data: list of keys to be stored (optional)
								 * path - the key - see AVNApi.addData, all pathes starting with "gps." will be sent to the GUI
								 * description
		"""
		return {
			'description': 'download overlays',
		}
	CONFIG_URL={
			'name':'url',
			'description':'url to get overlay file from',
			'default':'http://wscm4-01:8000/',
			'type': 'STRING'
		}
	CONFIG_INTERVAL={
		'name':'interval',
		'description':'query interval(s)',
		'default': 900,
		'type': 'NUMBER',
		'rangeOrList':[2,3600]
	}

	def __init__(self,api):
		"""
				initialize a plugins
				do any checks here and throw an exception on error
				do not yet start any threads!
				@param api: the api to communicate with avnav
				@type	api: AVNApi
		"""
		self.api = api # type: AVNApi
		self.api.registerEditableParameters([self.CONFIG_URL, self.CONFIG_INTERVAL],self.changeConfig)

	def changeConfig(self,newValues):
		self.api.saveConfigValues(newValues)

	def run(self):
		"""
		the run method
		this will be called after successfully instantiating an instance
		this method will be called in a separate Thread
		The example simply counts the number of NMEA records that are flowing through avnav
		and writes them to the store every 10 records
		@return:
		"""
		self.api.log("started")
		self.api.setStatus('STARTED','running')
		outDir=os.path.join(self.api.getDataDir(),'overlays')
		if not os.path.isdir(outDir):
			os.makedirs(outDir,0o775)
		if not os.path.isdir(outDir):
			raise Exception("unable to create overlay dir %s"%outDir)
		lastWritten=None
		count=0
		lastQuery=0
		while not self.api.shouldStopMainThread():
			interval=self.api.getConfigValue(self.CONFIG_INTERVAL.get('name'),self.CONFIG_INTERVAL.get('default'))
			interval=float(interval)
			now=time.monotonic()
			if lastQuery is None:
				lastQuery= now - interval -1 #ensure immediate at beginning
			#wait for next query interval
			#use monotonic timer to cope with time changes
			while now < (lastQuery + interval):
				if self.api.shouldStopMainThread():
					break
				time.sleep(0.5)
				now=time.monotonic()
			lastQuery=now
			url=self.api.getConfigValue(self.CONFIG_URL.get('name'),self.CONFIG_URL.get('default'))
			if url is None or url == "":
				self.api.setStatus('ERROR',"no parameter url set")
				continue
			try:
				response=urllib.request.urlopen(url)
				if response is None:
					raise Exception("empty response")
				data=response.read()
				navtex_response = json.loads(data)
				for i in range(len(navtex_response['Folder'])):
					response=urllib.request.urlopen(url + 'read/' + str(i))
					if response is None:
						raise Exception("empty response read " + str(i))
					data=response.read()
					# die Quotes an Anfang und Ende müssen weg.
					of = 'Navtex_default'
					for ppart in navtex_response['Folder'][i].split('/'):
						if len(ppart) > 0:
							of = ppart + '.geojson'
					count+=1
					lastWritten=self.safeWrite(os.path.join(outDir,of),data,True)
					self.api.setStatus("Navtex","(%d) %s updated %s"%(count,of,time.strftime("%Y/%m/%d %H:%M:%S",time.localtime(lastWritten))))
			except Exception as e:
				count=0
				self.api.setStatus("ERROR","unable to fetch %s: %s"%(url,str(e)))

	def safeWrite(self,fileName: str,data: bytes,check:bool=True):
		'''
		write a file in a safe manner by first writing to a tmp file and using "replace" afterwards
		to atomically change the existing file
		this ensures that the file has always a valid content
		:param fileName: the file name to write to
		:param data: the data to be written
		:param check: if True only write to the file if the content has changed
		:return: modification time
		'''
		if check:
			try:
				if os.path.isfile(fileName):
					with open(fileName,"rb") as fh:
						old=fh.read()
						if old == data:
							st=os.stat(fileName)
							return st.st_mtime
			except:
				pass
			tmpName=fileName+".tmp"
			try:
				os.unlink(tmpName) #maybe left from previous
			except:
				pass
			try:
				with open(tmpName,"wb") as wh:
					wh.write(data)
					wh.close()
				os.replace(tmpName,fileName)
			except:
				try:
					os.unlink(tmpName)
				except:
					pass
				raise
			return os.stat(fileName).st_mtime
