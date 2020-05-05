#!/usr/bin/env python3
#

import requests
import json
import csv
from os import path
from datetime import datetime, timedelta
from time import sleep


class Settings:
    def __init__(self):
        with open("settings.json", "r") as settings_file:
            self.settings = json.load(settings_file)

    def __getattr__(self, item):
        return self.settings.get(item)


class Flight:
    # Map field names to array index in the flight data
    fields = {"icao24": 0,
              "callsign": 1,
              "origin_country": 2,
              "time_position": 3,
              "last_contact": 4,
              "longitude": 5,
              "latitude": 6,
              "baro_altitude": 7,
              "on_ground": 8,
              "velocity": 9,
              "true_track": 10,
              "vertical_rate": 11,
              "sensors": 12,
              "geo_altitude": 13,
              "squawk": 14,
              "api": 15,
              "position_source": 16
              }

    def __init__(self, flight_data):
        self.data = flight_data

    def get(self, item, default):
        return self.__getattr__(item)

    def __getattr__(self, item):
        if item in ["time_position", "last_contact"]:
            timestamp = self.data[self.fields.get(item)]
            if timestamp is not None:
                return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

        if item == 'keys':
            return self.fields.keys

        return self.data[self.fields.get(item)]

    def __iter__(self):
        for field in self.fields.keys():
            yield field, self.__getattr__(field)


# Remember flight codes for 'duration' seconds
class DeDuplicator:
    def __init__(self, filename, duration):
        self.filename = filename
        self.duration = duration  # In seconds
        if path.exists(self.filename):
            with open(self.filename, "r") as history_file:
                self.seen = json.load(history_file)
        else:
            self.seen = {}

    def remember(self, flight):
        self.seen[flight.icao24] = int(datetime.now().timestamp())
        with open(self.filename, "w+") as history_file:
            history_file.write(json.dumps(self.seen))

    def have_seen(self, flight):
        # Expire all records older than self.duration minutes
        to_remove = []
        for entry, dt in self.seen.items():
            if dt < datetime.now().timestamp() - self.duration:
                to_remove.append(entry)
        for entry_to_remove in to_remove:
            del self.seen[entry_to_remove]

        return flight.icao24 in self.seen


class CsvLogger:
    # Filename can contain datetime format specifiers like %M
    def __init__(self, filename):
        self.filename = filename

    def current_filename(self):
        return datetime.now().strftime(self.filename)

    # Logs a Flight object to CSV
    def log(self, flight):
        filename = self.current_filename()
        write_header = not path.exists(filename)
        with open(filename, "a+") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=Flight.fields.keys(), quoting=csv.QUOTE_NONNUMERIC)
            if write_header:
                writer.writeheader()
            writer.writerow(flight)


class FileLogger:
    def __init__(self, filename):
        self.filename = filename

    def log(self, text):
        with open(self.filename, "a+") as logfile:
            logfile.write(text + "\n")


class Scraper:
    def __init__(self):
        self.settings = Settings()
        self.log = FileLogger(self.settings.log_file)
        self.csv = CsvLogger(self.settings.csv_file)
        self.dedup = DeDuplicator(self.settings.history_file, self.settings.keep_history)

    def poll_url(self):
        url = f"{self.settings.api_url}/states/all?lamin={self.settings.lamin}&lomin={self.settings.lomin}&lamax={self.settings.lamax}&lomax={self.settings.lomax}"
        if self.settings.username != "":
            auth = (self.settings.username, self.settings.password)
            response = requests.get(url, auth=auth)
        else:
            response = requests.get(url)

        self.log.log(response.content.decode())

        if not response.ok:
            self.log.log(f"Probleem bij het opvragen van API gegevens: {response.content}")
            return

        flights = response.json()
        if 'states' not in flights or flights['states'] is None:
            # No flight data within the given region
            return

        for flight_data in flights['states']:
            flight = Flight(flight_data)
            # Check and filter altitude
            if flight.geo_altitude is not None:
                if flight.geo_altitude > self.settings.max_geo_altitude:
                    # Flight is above maximum altitude > skip this record
                    continue

            # Flight should be logged, but only not previously logged
            if not self.dedup.have_seen(flight):
                self.csv.log(flight)
                self.dedup.remember(flight)

    def run(self):
        while True:
            self.poll_url()
            sleep(self.settings.poll_interval)


if __name__ == '__main__':
    scraper = Scraper()
    scraper.run()
