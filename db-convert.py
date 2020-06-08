#!/usr/bin/env python3
#

from datetime import datetime, timedelta
from os import path
import argparse
import glob
import csv
import functools

TIME_RANGE = 180


class FlightsReader:

    def __init__(self, filename):
        with open(filename, "r") as flights_csv_file:
            self.flights = [flight for flight in csv.DictReader(flights_csv_file)]

    def __iter__(self):
        for flight in self.flights:
            yield flight


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
            writer = csv.DictWriter(csv_file, fieldnames=flight.keys(), quoting=csv.QUOTE_NONNUMERIC)
            if write_header:
                writer.writeheader()
            writer.writerow(flight)


class AudioDatabase:
    def __init__(self, filename):
        self.filename = filename
        self.samples = self._read_db_file()

    @property
    @functools.lru_cache()
    def station_id(self):
        fn = self.filename.lower().replace('.wwx', '')
        return fn.split('-')[-1]

    def sample_to_dict(self, index):
        start_time = datetime(hour=0, minute=0, second=0, year=2020, day=1, month=1)
        return {
            f"tijd": (start_time + timedelta(seconds=index)).strftime("%H:%M:%S"),
            f"dba": self.get_sample(index)
        }

    def get_sample(self, index):
        sample = self.samples[index]
        if sample >= 128:
            sample -= 128
        return sample

    def _read_db_file(self):
        with open(self.filename, "rb") as database:
            samples = database.read()
        return samples

    def find_highest_sample(self, timerange_start, timerange_end):
        # Scan through all the audio samples for this time range, find the max value
        max_dba_index = 0
        for index in range(timerange_start, timerange_end):
            sample = self.get_sample(index)
            if sample > self.get_sample(max_dba_index):
                max_dba_index = index

        return self.sample_to_dict(max_dba_index)


class Matcher:
    def __init__(self, config):
        self.source_file = config.input
        self.wwx_directory = config.wwxpath
        self.csv_writer = CsvLogger(config.output)

    @staticmethod
    def add_empty_dba_info(flight):
        for station in range(1, config.max_stations+1):
            station_id = str(station).zfill(3)
            flight.update(
                {
                    f'tijd-{station_id}': '00:00',
                    f'dba-{station_id}': 0
                }
            )
        return flight

    def match(self):
        for flight in FlightsReader(self.source_file):
            dt = datetime.strptime(flight['time_position'], '%Y-%m-%d %H:%M:%S')
            file_date = dt.strftime('%Y%m%d')
            wwx_filenames = sorted(glob.glob(f'{self.wwx_directory}/*{file_date}-*.wwx'))

            if len(wwx_filenames) == 0:
                # No WWX file found for this flight
                print(f"Warning: No WWX file found for date {file_date} in directory {self.wwx_directory}")
                self.csv_writer.log(flight)
                continue

            flight = self.add_empty_dba_info(flight)
            for filename in wwx_filenames:
                audio = AudioDatabase(filename)
                time_index_start = (dt - datetime(dt.year, dt.month, dt.day, 0, 0, 0)).seconds - TIME_RANGE
                sample = audio.find_highest_sample(time_index_start, time_index_start + 2 * TIME_RANGE)
                flight.update({
                    f'tijd-{audio.station_id}': sample['tijd'],
                    f'dba-{audio.station_id}': sample['dba']
                })

            self.csv_writer.log(flight)


class Converter:
    def __init__(self, config):
        self.config = config

    def convert(self):
        audio = AudioDatabase(self.config.input)
        csv_writer = CsvLogger(self.config.output)
        for index in range(0, 86400):
            csv_writer.log(audio.sample_to_dict(index))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Match en conversie tool voor vluchtinformatie en WWX bestanden')
    subparsers = parser.add_subparsers(title='acties', help='Uit te voeren actie', dest='action')
    match_parser = subparsers.add_parser('match')
    match_parser.add_argument('--input', help='CSV bestand met vluchtinformatie zoals geschreven door opensky-scraper',
                              required=True)
    match_parser.add_argument('--output', help='CSV bestand waarin vluchtinfo met dBA waarden geschreven wordt',
                              required=True)
    match_parser.add_argument('--wwxpath',
                              help='Directory waar WWX bestanden zijn opgeslagen die overeenkomen met de vluchtinfo CSV',
                              required=True)
    match_parser.add_argument('--max-stations', help='Maximaal aantal meetstations waarvoor WWX bestanden beschikbaar zijn',
                              default=16, dest='max_stations')

    convert_parser = subparsers.add_parser('convert')
    convert_parser.add_argument('--input', help='WWX bestand om te converteren naar CSV formaat', required=True)
    convert_parser.add_argument('--output', help='CSV bestand voor schrijven van geconverteerde WWX data', required=True)

    config = parser.parse_args()

    if config.action == 'convert':
        converter = Converter(config)
        converter.convert()
    elif config.action == 'match':
        matcher = Matcher(config)
        matcher.match()
    else:
        parser.print_help()
