#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "Please run as root (i.e. sudo)"
  exit
fi
TARGETDIR=/svc/navtex-parser
TARGETSRC=${TARGETDIR}/src/Navtex
mkdir -p $TARGETDIR
cp src/Navtex/*.py ${TARGETSRC}/
cp Navtex.service ${TARGETDIR}/
pip install uvicorn
pip install FastAPI
sudo systemctl enable ${TARGETDIR}/Navtex.service