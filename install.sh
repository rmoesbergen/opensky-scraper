#!/bin/bash
#

sudo apt-get -yy update
sudo apt-get -yy install python3-requests python3-tz

wget https://raw.githubusercontent.com/rmoesbergen/opensky-scraper/master/opensky-scraper.py -O /home/pi/opensky-scraper.py
wget https://raw.githubusercontent.com/rmoesbergen/opensky-scraper/master/opensky-scraper.service -O /home/pi/opensky-scraper.service
wget https://raw.githubusercontent.com/rmoesbergen/opensky-scraper/master/opensky-scraper-luik.service -O /home/pi/opensky-scraper-luik.service

if [[ ! -f settings.json ]]; then
  wget https://raw.githubusercontent.com/rmoesbergen/opensky-scraper/master/settings.json -O /home/pi/settings.json
else
  echo "Keeping existing configuration file"
fi

if [[ ! -f settings-luik.json ]]; then
  wget https://raw.githubusercontent.com/rmoesbergen/opensky-scraper/master/settings-luik.json -O /home/pi/settings-luik.json
else
  echo "Keeping existing Luik configuration file"
fi

sudo mv /home/pi/opensky-scraper.service /etc/systemd/system/opensky-scraper.service
sudo mv /home/pi/opensky-scraper-luik.service /etc/systemd/system/opensky-scraper-luik.service
sudo chown root:root /etc/systemd/system/opensky-scraper.service
sudo chown root:root /etc/systemd/system/opensky-scraper-luik.service

sudo systemctl daemon-reload
sudo systemctl enable opensky-scraper.service
sudo systemctl enable opensky-scraper-luik.service
