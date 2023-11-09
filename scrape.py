#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
#from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import requests
import time
import pandas as pd
import re	#needed for regex calls
from tqdm import tqdm	#needed for loading bar on CLI
import argparse	#needed for parsing commandline arguments
import csv	#for writing to file

#Helper functions

purge_these_certs = []

def ask_user(question):
	answer = input(question + " (y/n): ").lower().strip()
	print("")
	while not(answer == "y" or answer == "yes" or answer == "n" or answer == "no"):
		print("Input yes or no")
		answer = input(question + "(y/n): ").lower().strip()
		print("")
	if answer[0] == "y":
		return True
	else:
		return False
		
def restricted_float(x):
	try:
		x = float(x)
	except ValueError:
		raise argparse.ArgumentTypeError("%r not a floating-point literal" % (x,))
	return x

def write_results_to_file(filename, j_id, j_title, j_certs):
	with open(f'{filename}_allinfo.csv', 'a+') as f:
		#writer = csv.DictWriter(f, fieldnames = header)
		#writer.writeheader()
		#writer.writerow({'job_id': j_id, 'job_title' : j_title, 'certifications' : j_certs})
		f.write(f'{j_id[0]},{j_title[0]},{j_certs}\n')

def write_csv(filename, j_id, j_title, cert):
	with open(f'{filename}_data.csv', 'a+') as f:
		#writer = csv.DictWriter(f, fieldnames = header)
		#writer.writeheader()
		#writer.writerow({'job_id': j_id, 'job_title' : j_title, 'certifications' : j_certs})
		f.write(f'{j_id},{j_title},{cert}\n')
		
def store_dict(filename, dic):
	csv_cols = ['certification','count']
	with open(f'{filename}_certs.csv', 'a+') as f:
		for key in dic.keys():
			f.write("%s,%s\n"%(key,dic[key]))
		

#Configure command line arguments
argp = argparse.ArgumentParser(description="Web Scraper meant for scraping certification information as it relates to InfoSec jobs off of LinkedIn")
argp.add_argument("-j", "--job", help="The job title or keyword to search for", default="cybersecurity")
argp.add_argument("-t", "--time", choices=['day', 'week', 'month', 'all'], help="How recent the listings to be scraped should be", default="all")
argp.add_argument("-s", "--seniority", type=list, help="The levels of seniority (1-5, least to greatest) to process as input: each level should be explicitly named for inclusion (e.g. for all levels, input is '12345'", default="1")
argp.add_argument("-l", "--location", help="The geographic area to consider jobs. Default is 'remote'", default="remote")
argp.add_argument("-i", "--increment", help="The increment of time in seconds that should be allowed to let jobs load for scraping", type=restricted_float, default=0.5)
argp.add_argument("-o", "--output", help="The name of the file to output scrape results to")
argp.add_argument("-q", "--quick", help="Only parse the first 100 results", action='store_true')
argp.add_argument("-k", "--keywords", help="A list of keywords to more narrowly filter LinkedIn's search results; excludes any job titles that do NOT have any of the listed keywords", default="")
argp.add_argument("--max", help="The maximum number of jobs that should be processed", type=int)



parsed=argp.parse_args()

timeDic = {
	"day": "r86400",
	"week": "r604800",
	"month": "r2592000",
	"all" : ""
}

timeWindow = timeDic[parsed.time]

seniority = ','.join(parsed.seniority)

filterwords = (parsed.keywords).lower().split()

IBlack="\033[0;90m"       # Black
IRed="\033[0;91m"         # Red
IGreen="\033[0;92m"       # Green
IYellow="\033[0;93m"      # Yellow
IBlue="\033[0;94m"        # Blue
IPurple="\033[0;95m"      # Purple
ICyan="\033[0;96m"        # Cyan
IWhite="\033[0;97m"       # White

cert_dic = {}


try:
	#keyword 'cybersecurity' located 'remote'
	#cyber_url = 'https://www.linkedin.com/jobs/search?keywords=Cybersecurity&location=remote&geoId=&trk=public_jobs_jobs-search-bar_search-submit&position=1&pageNum=0'
	
	cyber_url = f'https://www.linkedin.com/jobs/search?keywords={parsed.job}&location={parsed.location}&geoId=&trk=public_jobs_jobs-search-bar_search-submit&f_TPR={timeWindow}&f_E={seniority}&position=1&pageNum=0'
	
	#pentester
	#cyber_url = 'https://www.linkedin.com/jobs/search?keywords=pentester&location=United%20States&geoId=&trk=public_jobs_jobs-search-bar_search-submit&position=1&pageNum=0'

	#fireFoxOptions = Options()
	#fireFoxOptions.add_argument("--headless")
	#ffoptions = webdriver.FirefoxOptions()
	#ffoptions.set_headless()
	#ffoptions.add_argument("--headless")
	#wd = webdriver.Firefox(executable_path='/home/kali/LinkedInfoSec/geckodriver')
	#wd = webdriver.Firefox(firefox_options=ffoptions)
	service = Service(executable_path='/snap/bin/firefox.geckodriver')
	wd = webdriver.Firefox(service=service)

	#Getting cyber-related jobs
	wd.get(cyber_url)

	#This pulls the total number of search results from the DOM, strips the "+" and ',' characters, then casts as an int
	str_of_cyberjobs = str(wd.find_element(By.CSS_SELECTOR,'h1>span').get_attribute('innerText'))
	str_of_cyberjobs = str_of_cyberjobs.replace('+','')
	no_cyberjobs = int(str_of_cyberjobs.replace(',', ''))
	if parsed.max is not None and no_cyberjobs > parsed.max:
		no_cyberjobs = parsed.max

	#print(f"# of cybersecurity jobs: {no_cyberjobs}")
	
	"""
	question = f"The certscraper has found {no_cyberjobs} to scrape, do you want to proceed?"
	if not ask_user(question):
		exit()
	"""
	
	#scroll through jobs listings
	jobs_iteration = 0
	if parsed.quick:
		jobs_iteration = 1
	else:
		jobs_iteration = (no_cyberjobs//25)+1
	for i in tqdm(range(jobs_iteration)):
		wd.execute_script('window.scrollTo(0,document.body.scrollHeight);')
		#if parsed.quick and i > 2:
		#	break
		#i = i + 1
		try:
			#Looking for the "See More Jobs" button that eventually appears when scrolling through job listings
			found = len(wd.find_elements(By.CLASS_NAME, 'infinite-scroller__show-more-button--visible'))
			if found > 0:
				#time.sleep(1)
				wd.find_element(By.CLASS_NAME, 'infinite-scroller__show-more-button--visible').click()
				#time.sleep(0.5)
			else:
				time.sleep(1)
				#WebDriverWait(wd, 5).until(EC.element_to_be_clickable((By.XPATH, "By.CLASS_NAME, 'infinite-scroller__show-more-button--visible'")))
				
		except:
			time.sleep(1)
			pass
			
	#Find all jobs
	job_list = wd.find_element(By.CLASS_NAME, 'jobs-search__results-list')
	#Look at each job
	jobs = job_list.find_elements(By.TAG_NAME, 'li')
	print(f'The number of jobs actually to be processed: {len(jobs)}')
	
	job_id = []
	job_title = []
	job_location = []
	job_age = []
	job_num = 1
	failed_jobs = 0	#The number of jobs that failed to load for web scraping
	no_certs = 0	#the number of jobs scraped where certs weren't found
	yes_certs = 0	#The number of jobs scraped where certs were found
	may_certs = 0	#The number of jobs scraped where certs may exist with closer inspection
	job_tracker = 0 #Tracks how many jobs we've observed so far
	
	#cert_dic = {}
	
	#TODO, fix tqdm to reflect -q option
	#TODO, implement interrupt function to allow user to change speed of jobs processing on-the-fly
	
	#Enumerating jobs
	for job in tqdm(jobs):
		#print(IWhite + f"\n[+] Now listing JOBID: {job_id}, {job_title}:")
		
		#Pulling information from the job description by clicking through each job
		#Reference for fetching XPATH: https://www.guru99.com/xpath-selenium.html
		"""job_link = f"/html/body/div[1]/div/main/section[2]/ul/li[{job_num}]/*"
		#print(job_link)
		try:
			wd.find_element(By.XPATH, job_link).click()
		except:
			job_num += 1
			continue"""
		#The first several jobs are particularly relevant to the -j flag
		#Subsequent results are less important and don't need as much attention
		"""if job_num < 50:
			#WebDriverWait(wd, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/section/div[2]/section/div/div[1]/div/div/a")))
			#time.sleep(2)
			
			try:
				#WebDriverWait(wd, parsed.increment).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/section/div[2]/section/div/div[1]/div/div/a")))
				WebDriverWait(wd, parsed.increment).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/section/div[2]/section/div/div[1]/div/div/button[1]")))
			except:
				job_num += 1
				print(IRed + f"[-] Failed to render job listing. Try slowing down rate with -i." + IWhite)
				continue
			
		else:
			if parsed.quick:
				break
			#time.sleep(parsed.increment)
			try:
				#WebDriverWait(wd, {parsed.increment}).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/section/div[2]/section/div/div[1]/div/a")))
				WebDriverWait(wd, parsed.increment).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[0]/div/section/div[1]/section")))
			except:
				print("F2")
				job_num += 1
				continue"""
		#print("IT WORKED")
		j_id = job.find_element(By.CLASS_NAME, 'job-search-card').get_attribute('data-entity-urn')
		j_id = str(j_id).replace('urn:li:jobPosting:','')
		j_title = job.find_element(By.CLASS_NAME, 'base-search-card__title').get_attribute('innerText')
		j_location = job.find_element(By.CLASS_NAME, 'job-search-card__location').get_attribute('innerText')
		j_age = job.find_element(By.TAG_NAME, 'time').get_attribute('innerText')
		job_id.append(j_id)
		job_title.append(j_title)
		job_location.append(j_location)
		job_age.append(j_age)
		job_num = job_num + 1

		if len(filterwords) > 0:
			t_title = j_title.lower()
			isGood = False
			for kword in filterwords:
				if kword in t_title:
					isGood = True
			if not isGood:
				continue
		#job_desc_block = "/html/body/div[1]/div/section/div[2]/div[1]/section[1]/div/div[2]/section/div"
		#print(job_num,j_id,j_title,j_age)
		
		#This is the XPATH to the descriptive text
		job_desc_block = "/html/body/div[1]/div/section/div[2]/div/section[1]/div/div/section/div"
		#job_desc_block = "/html/body/div[1]/div/section/div[2]/div/section[2]/div/div/section/div"
				
		#Sometimes the script doesn't sleep long enough for text to load; we don't want to preemptively terminate the script, so this is a check to see if it's loaded.
		found = len(wd.find_elements(By.XPATH, job_desc_block))
		if found > 0:
			jd_block = wd.find_element(By.XPATH, job_desc_block).get_attribute('innerHTML')
			#print(jd_block)
		else:
			failed_jobs += 1
			continue
		
		keywords = ["certification", "certifications", "certs", "Certification", "Certifications", "Certs", "accreditations", "accreditation", "Certification(s)", "certification(s)"]
		jd_certs = set()
		
		### FIND KEYWORDS ###
		# Replace this URL with the one you want to request
		#url = "https://www.linkedin.com/jobs/search?currentJobId=3716710886"
		j_url = "https://www.linkedin.com/jobs/view/" + j_id

		# Send a GET request to the URL
		response = requests.get(j_url)
		foundcert = False

		# Check if the request was successful (status code 200)
		if response.status_code == 200:
			# Print the response content (the web page HTML, for example)
			#print(response.text)

			# Define the keywords you want to search for
			keywords = ["certification", "certifications", "certs", "Certification", "Certifications", "Certs", "accreditations", "accreditation", "Certification(s)", "certification(s)"]

			# Regular expression pattern to match any of the keywords
			keyword_pattern = "|".join(re.escape(keyword) for keyword in keywords)
			pattern = re.compile(keyword_pattern, re.I)  # 're.I' for case-insensitive matching

			# Regular expression pattern to match words with "+" or at least 2 consecutive uppercase letters
			#word_pattern = re.compile(r"\b(?:[A-Z]{2,}|\w+\+\w+\d+|\w+-\d+)(?![A-Z-])")
			word_pattern = re.compile(r"[A-Z]+\-+[\w]+|[a-zA-Z]+\+|[\w]+[A-Z]{2,}")

			
			# Iterate through the response content line by line
			for line in response.iter_lines(decode_unicode=True):
				if pattern.search(line):
					matching_words = word_pattern.findall(line)
					if matching_words:
						#print("Matching Line:", line)
						#print("Matching Words:", matching_words)
						#csvset = (matchin)
						foundcert = True

						for cred in set(matching_words):
							write_csv(parsed.output, j_id, j_title, cred)
						jd_certs.update(matching_words)
		else:
			#print(f"Failed to retrieve the page. Status code: {response.status_code}")
			pass

		"""if (jd_certs == set()):
			no_certs += 1
		else:
			yes_certs += 1"""
		if foundcert:
			yes_certs += 1
		else:
			no_certs += 1
		
		
		
		job_tracker += 1
		write_results_to_file(parsed.output, [j_id], [j_title], jd_certs)
		
		for cert in jd_certs:
			if cert in cert_dic:
				cert_dic[cert] += 1
			else:
				cert_dic[cert] = 1
				
		if job_tracker == 50:
			res = dict(sorted(cert_dic.items(), key=lambda x: (-x[1], x[0])))
			store_dict(f'{parsed.output}_first50', res)
		#print(IWhite + str(jd_certs))

	#wd.find_element(By.CLASS_NAME, 'jobs-search__results-list')
	#print(job_id)
	print(IRed + f"[-] A total of {failed_jobs} jobs failed to load while scraping, consider slowing the rate of processing with the -i flag")
	print(IGreen + f"[+] A total of {no_certs} jobs did not have any certs found")
	print(IGreen + f"[+] A total of {yes_certs} jobs did have certs listed")
	
	res = dict(sorted(cert_dic.items(), key=lambda x: (-x[1], x[0])))
	store_dict(f'{parsed.output}_all', res)
	
	for k,v in res.items():
		print(f"{k} : {v}")
	print(f"{yes_certs} jobs had certs listed, {no_certs} did not list any certs or could not be loaded.")
except KeyboardInterrupt:
	print(IRed + "[-] CTRL+C detected! Terminating")
	res = dict(sorted(cert_dic.items(), key=lambda x: (-x[1], x[0])))

	for k,v in res.items():
		print(f"{k} : {v}")
	
finally:
	try:
		wd.close()
	except:
		pass
