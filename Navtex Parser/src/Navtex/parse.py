#!/usr/local/bin/python2.7
# encoding: utf-8
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

import sys
import json

from Navtex.MessageParser import MessageParser

__all__ = []
__version__ = 0.1
__date__ = '2023-04-25'
__updated__ = '2023-04-25'


def main(argv):
	config = '../config.txt'
	if argv[1]:
		config = argv[1]
	with open(config, 'r') as confile:
		folders = [folder.strip() for folder in confile if not folder[0] == '#']

	targetpath = '/home/pi/avnav/data/overlays'
	if argv[2]:
		targetpath = argv[2]
	mp = MessageParser(folders, verbose=False)
	mp.parseAll()
	for name, msgs in mp.messageLists.items():
		with open(targetpath +'/' + name + ".geojson", "w") as ofile:
			ofile.write(json.dumps(msgs, indent=2))
		

if __name__ == "__main__":
	sys.exit(main(sys.argv))
	