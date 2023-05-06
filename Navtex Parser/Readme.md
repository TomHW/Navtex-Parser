This plugin for [AvNav](https://www.wellenvogel.net/software/avnav/docs/beschreibung.html?lang=en) provides map overlays from Navtex messages.

Some Navtex messages (especially message type A) contain positions that can be located on a map. This can be drifting buoys, military execises, dredging or any other activity that affects safe traffic. The plugin loads the Navtex messages from a local Navtex receiver or from internet locations (url). The local receiver should provide the messages as plain text files. I'm using Mörer's WIB2 connected via USB. Navtex internet pages embed the messages in Html pages that require extracting the messages from Html. Each provider has its own format that needs special parsing. This repository comes with an Html parser for German Navtex messages from DWD. Feel free to write your own parser for your preferred Navtex site.

AvNav often runs on chart plotters located in the boat cockpit and it is disturbing to have many firmly attached hardware to the plotter. Hence the parser consists of a server that has an API that provides the position oriented messages and an AvNav plugin that reads the messages and writes overlay files. If you don't need the API and prefer a local parser, you can run the service in local mode (writes overlay files directly).

Installation
============
Depending on your preferred installation mode proceed with one of the following sections.

API mode
--------
Clone the repository to a local folder and start ./install.sh. This will load the necessary Python modules and create a service that establishes the API. The file `config.txt` contains the message sources (local folders or urls).

	srv
	└── navtex-parser
	    ├── Navtex.service
	    └── src
	        ├── config.txt
	        └── Navtex
	            ├── API.py
	            ├── __init__.py
	            ├── MessageParser.py
	            └── parse.py

Edit the `config.txt` file for you needs, each line contains a local file path or an url. You can comment out a line with a `#` in the first column. Save the file and start the service:

	sudo systemctl start Navtex.service

You should be able to test the API with a browser. Call `http://<myServer>:8000`, this should show the list of configured message sources (json).

	Folder	
	0	"/media/pi/WIB2/INTERNAT"
	1	"/media/pi/WIB2/NATIONAL"
	2	"https://www.dwd.de/DE/fachnutzer/schifffahrt/funkausstrahlung/navtex/518_ros.html"

A call to `http://<myServer>:8000/read/<n>` responds with geojson data from the selected folder. `<n>` is the number of the folder.

On your AvNav machine you should create a plugin folder: `~/avnav/data/plugins/Navtex/` and if not present create also `~/avnav/data/overlays/`. Copy the file `plugin.py` into the new plugin folder and open it with a text editor. In line 46 change the url to the name of your Navtex-API-server. Line 52 holds the update time interval. For test purposes it is convenient to work with short intervals, but in practice it is sufficient to check each quarter or each hour, because Navtex messages are updated in 4 hour time slots. Save `plugin.py` and restart the avnav service. If everything is configured correctly, your should find new files in the overlays folder (one for each line in your `config.txt`'s server file)

Local mode
----------
Clone the repository to a local folder and create a `crontab` entry.

	*/15 * * * * python3 /<path to your folder>/parse.py <config-file> <output-folder>
	
This should update your overlay files every 15 minutes.

Visualization in AvNav
======================
Follow the instructions for [chart overlays](https://www.wellenvogel.net/software/avnav/docs/hints/overlays.html?lang=en#h2:Configuration) in AvNav. Use `type` overlay and select an overlay from your created geojson files. Add the 'featureFormatter` genericHtmlInfo.

![Overlay configuration](./images/Edit%20Overlay%20AVNav-Web.png)

Now your map should show the positions of messages:

![Map with overlays](./images/Chart%20with%20Overlay%20AVNav-Web.png)

Click on a point or in an area to see details:

![Message details](./images/Overlay%20Info%20AVNav-Web.png)

Some Notes
==========
Please consider that Navtex messages are transmitted by SITOR-B with error correction (FEC), but errors are still possible in poor reception conditions. Therefore positions are missing in some messages or messages are omitted due to not readable positions.

A message with one position is presented as point. Two positions in a message result in two points on the map or a line when the keyword TRACK occurs in the message. From three positions on you will see the points, lines connecting the points when the keyword TRACK occurs in the message or a polygon when the keyword AREA occurs in the message.
