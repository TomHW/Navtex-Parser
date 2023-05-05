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
import re
from fastapi import FastAPI

from Navtex.MessageParser import MessageParser

#folders = ['/media/sesth/WIB2/NATIONAL', '/media/sesth/WIB2/INTERNAT']
with open('config.txt', 'r') as confile:
	folders = [folder.strip() for folder in confile if not folder[0] == '#']

mp = MessageParser(folders, verbose=False)

app = FastAPI()

@app.get("/")
async def root():
	return {"Folder": folders}

@app.get("/read/{folderNo}")
async def read_overlay(folderNo : int):
	if(folderNo >= 0 and folderNo < len(folders)):
		if m := re.match(r'^\s*https?://([^/]+)/.*', folders[folderNo]):
			geojson = mp.parse_html(folders[folderNo])
		else:
			geojson = mp.iterate_directory(folders[folderNo])
		return geojson
	
	
