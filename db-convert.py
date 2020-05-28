#!/usr/bin/env python3
#

from datetime import datetime, timedelta
from sys import argv
from os import path
import csv


class CsvLogger:
    FIELDS = [
        "tijd", "dba", "overflight"
    ]

    # Filename can contain datetime format specifiers like %M
    def __init__(self, filename):
        self.filename = filename

    def current_filename(self):
        return datetime.now().strftime(self.filename)

    # Logs a Flight object to CSV
    def log(self, sample):
        filename = self.current_filename()
        write_header = not path.exists(filename)
        with open(filename, "a+") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.FIELDS, quoting=csv.QUOTE_NONNUMERIC)
            if write_header:
                writer.writeheader()
            writer.writerow(sample)


class DbConverter:
    def __init__(self, filename):
        self.filename = filename
        self.csv_writer = CsvLogger(f'{filename}.csv')

    def convert(self):
        with open(self.filename, "rb") as database:
            samples = database.read()
            start_time = datetime(hour=0, minute=0, second=0, year=2020, day=1, month=1)
            samples = samples[0:86400]
            for sample in samples:
                if sample > 128:
                    overflight = True
                    sample -= 128
                else:
                    overflight = False
                self.csv_writer.log({
                    "tijd": start_time.strftime("%H:%M:%S"),
                    "dba": sample,
                    "overflight": overflight
                })
                start_time += timedelta(seconds=1)


if __name__ == '__main__':
    converter = DbConverter(argv[1])
    converter.convert()
