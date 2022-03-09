# LinkedInfoSec README

The LinkedInfoSec project was born from the desire to identify exactly which certifications prospective employers are looking for right now. The tool datascrapes LinkedIn's public-facing job search endpoint for job listings that contain certifications, then outputs .CSV formatted files with all of the information it grabs.

The python script requires the following non-standard libraries and their dependencies:

1. selenium
2. tqdm
3. argparse

The following flags may be passed to scrape.py to tailor your results:

* **-j** or **--job**: The job title or keyword to search for. The default is "cybersecurity". Example: **python3 scrape.py -j "penetration tester"**
