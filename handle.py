#!/usr/bin/env python3

import argparse	#needed for parsing commandline arguments
import os.path
import re

argp = argparse.ArgumentParser(description="Web Scraper meant for scraping certification information as it relates to InfoSec jobs off of LinkedIn")
argp.add_argument("-f", "--file", help="The filename to open and parse")
parsed=argp.parse_args()

filename = parsed.file

if not os.path.exists(filename):
	argp.error("File doesn't exist")

d = {}

with open(f'{filename}', 'r') as f:
	lines = f.readlines()
	pattern = r"'([A-Za-z0-9_\./\\-]*)'"
	for line in lines:
		m = re.findall(pattern, line)
		if len(m) > 0:
			for e in m:
				if e in d:
					d[e] += 1
				else:
					d[e] = 1

res = dict(sorted(d.items(), key=lambda x: (-x[1], x[0])))
print(res)
		
	

"""
with open(f'pentester_certs.txt', 'r') as f:
	lines = f.readlines()
	certs = {}
	for line in lines:
		cert = line.split()
		for c in cert:
			if c in certs:
				certs[c] += 1
			else:
				certs[c] = 1
	res = dict(sorted(certs.items(), key=lambda x: (-x[1], x[0])))
	print(res)
"""