# LinkedInfoSec README

The LinkedInfoSec project was born from the desire to identify exactly which certifications prospective employers are looking for right now. The tool datascrapes LinkedIn's public-facing job search endpoint for job listings that contain certifications, then outputs .CSV formatted files with all of the information it grabs.

The python script requires the following non-standard libraries and their dependencies:

1. selenium
2. tqdm
3. argparse

The following flags may be passed to scrape.py to tailor your results:

* **-j** or **--job**: The job title or keyword to search for. The default is "cybersecurity". Example: **python3 scrape.py -j "penetration tester"**
* **-t** or **--time**: How recent the listings to be scraped should be. Example: **python3 scrape.py -t day**
* **-s** or **--seniority**: The leves of seniority (1-5, from Intern to Director-level) to process as input. Each level should be explicitly named for inclusion. Example: **python3 scrape.py -s 12345**
* **-l** or **--locations**: The geographic area to consider jobs. Default is 'remote'. Example: **python3 scrape.py -l "London"**
* **-i** or **--increment**: The increment of time (in seconds) that should be allowed to let jobs load for scraping. Example **python3 scrape.py -i 3**
* **-o** or **--output**: The name of the file to output scrape results to. Example **python3 scrape.py -o sec**
* **-q** or **--quick**: Only parse the first 50 listings. Example **python3 scrape.py -q**
* **-max**: The maximum number of jobs that should be processed. Example **python3 scrape.py --max 500**

Regardless of whether you specify a name for the outfile with (-o), the script puts out a .csv file with the results of the scrape, including the given LinkedIn jobID, job title, and the certs (if any) that were found to that post.

You can then output a sorted list of certifications by count by running **handle.py -f <file_allinfo.csv>**.
