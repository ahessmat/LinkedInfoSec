#!/usr/bin/env python3

from selenium import webdriver
#from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
import pandas as pd
import re	#needed for regex calls
from tqdm import tqdm	#needed for loading bar on CLI
import argparse	#needed for parsing commandline arguments
import csv	#for writing to file

#Helper functions
def ask_user(question):
	answer = input(question + "(y/n): ").lower().strip()
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

#Configure command line arguments
argp = argparse.ArgumentParser(description="Web Scraper meant for scraping certification information as it relates to InfoSec jobs off of LinkedIn")
argp.add_argument("-j", "--job", help="The job title or keyword to search for", default="cybersecurity")
argp.add_argument("-t", "--time", choices=['day', 'week', 'month', 'all'], help="How recent the listings to be scraped should be", default="all")
argp.add_argument("-s", "--seniority", type=list, help="The levels of seniority (1-5, least to greatest) to process as input: each level should be explicitly named for inclusion (e.g. for all levels, input is '12345'", default="1")
argp.add_argument("-l", "--location", help="The geographic area to consider jobs. Default is 'remote'", default="remote")
argp.add_argument("-i", "--increment", help="The increment of time in seconds that should be allowed to let jobs load for scraping", type=restricted_float, default=2)
argp.add_argument("-o", "--output", help="The name of the file to output scrape results to")
argp.add_argument("-q", "--quick", help="Only parse the first 100 results", action='store_true')



parsed=argp.parse_args()

print(f'Quick is {parsed.quick}')

print("OUTPUT FILE: ")
print(parsed.output)
print(type(parsed.output))

if parsed.output:
	print("PRESENT")
else:
	print("NOT")

timeDic = {
	"day": "r86400",
	"week": "r604800",
	"month": "r2592000",
	"all" : ""
}

timeWindow = timeDic[parsed.time]

seniority = ','.join(parsed.seniority)

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
	wd = webdriver.Firefox(executable_path='/home/kali/datascrape/geckodriver')
	#wd = webdriver.Firefox(firefox_options=ffoptions)

	#Getting cyber-related jobs
	wd.get(cyber_url)

	#This pulls the total number of search results from the DOM, strips the "+" and ',' characters, then casts as an int
	str_of_cyberjobs = str(wd.find_element_by_css_selector('h1>span').get_attribute('innerText'))
	str_of_cyberjobs = str_of_cyberjobs.replace('+','')
	no_cyberjobs = int(str_of_cyberjobs.replace(',', ''))

	#print(f"# of cybersecurity jobs: {no_cyberjobs}")
	
	question = f"The certscraper has found {no_cyberjobs} to scrape, do you want to proceed?"
	if not ask_user(question):
		exit()
	
	#scroll through jobs listings
	#i=2
	for i in tqdm(range((no_cyberjobs//25)+1)):
	#while i <= int(no_cyberjobs/25)+1:
	#while i <= 500:
		wd.execute_script('window.scrollTo(0,document.body.scrollHeight);')
		#i = i + 1
		try:
			#Looking for the "See More Jobs" button that eventually appears when scrolling through job listings
			found = len(wd.find_elements(By.CLASS_NAME, 'infinite-scroller__show-more-button--visible'))
			if found > 0:
				#time.sleep(1)
				wd.find_element(By.CLASS_NAME, 'infinite-scroller__show-more-button--visible').click()
			else:
				time.sleep(1)
				
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
	job_source = []
	job_num = 1
	failed_jobs = 0	#The number of jobs that failed to load for web scraping
	no_certs = 0	#the number of jobs scraped where certs weren't found
	yes_certs = 0	#The number of jobs scraped where certs were found
	may_certs = 0	#The number of jobs scraped where certs may exist with closer inspection
	
	#cert_dic = {}
	
	#Enumerating jobs
	for job in tqdm(jobs):
		j_id = job.find_element(By.CLASS_NAME, 'job-search-card').get_attribute('data-entity-urn')
		j_id = str(j_id).replace('urn:li:jobPosting:','')
		j_title = job.find_element(By.CLASS_NAME, 'base-search-card__title').get_attribute('innerText')
		j_location = job.find_element(By.CLASS_NAME, 'job-search-card__location').get_attribute('innerText')
		j_age = job.find_element(By.TAG_NAME, 'time').get_attribute('innerText')
		job_id.append(j_id)
		job_title.append(j_title)
		job_location.append(j_location)
		job_age.append(j_age)
		
		#print(IWhite + f"\n[+] Now listing JOBID: {j_id}, {j_title}:")
		
		#Pulling information from the job description by clicking through each job
		#Reference for fetching XPATH: https://www.guru99.com/xpath-selenium.html
		#job_link = f"/html/body/div[1]/div/main/section[2]/ul/li[{job_num}]/div"
		job_link = f"/html/body/div[1]/div/main/section[2]/ul/li[{job_num}]/*"
		wd.find_element(By.XPATH, job_link).click()
		if job_num < 100:
			time.sleep(3)
		else:
			if parsed.quick:
				break
			time.sleep(parsed.increment)
		job_num = job_num + 1
		#job_desc_block = "/html/body/div[1]/div/section/div[2]/div[1]/section[1]/div/div[2]/section/div"
		
		#This is the XPATH to the descriptive text
		job_desc_block = "/html/body/div[1]/div/section/div[2]/div/section[1]/div/div/section/div"
		#Sometimes the script doesn't sleep long enough for text to load; we don't want to preemptively terminate the script, so this is a check to see if it's loaded.
		found = len(wd.find_elements(By.XPATH, job_desc_block))
		"""
		job_check = "section.two-pane-serp-page__detail-view"
		wait = WebDriverWait(wd, 10)
		test_el = wd.switch_to.frame(wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, job_check))))
		#element = (wait.until(EC.visibility_of_element_located((By.XPATH, job_check))))
		#driver.switch_to.frame(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "turbo-checkout-iframe"))))
		
		
		print(found)
		i = 0
		while found < 1:
			time.sleep(1)
			found = len(wd.find_elements(By.XPATH, job_desc_block))
			i += 1
			if i > 5:
				failed_jobs += 1
				break
		"""
		if found > 0:
			jd_block = wd.find_element(By.XPATH, job_desc_block).get_attribute('innerHTML')
		else:
			failed_jobs += 1
			continue
		
		keywords = ["certification", "certifications", "certs", "Certification", "Certification", "Certs", "accreditations", "accreditation"]
		jd_certs = set()
		
		#Check if any of the of the keywords appear in the job description
		for keyword in keywords:
			key = f"//*[contains(text(), '{keyword}')]"
			found = len(wd.find_elements(By.XPATH, key))
			
			#If a keyword is found, scrutinize
			if found > 0:
				#print(IGreen + f"We found {found} instances of '{keyword}'")
				#Parse lines that have the keywords for certifications
				#Parse the line that has the keyword first
				jd_foundline = wd.find_element(By.XPATH, key)
				jd_foundlines = wd.find_elements(By.XPATH, key)
				for jd_foundline in jd_foundlines:
					sentence = jd_foundline.get_attribute('innerHTML')
					
					#Use regex to identify
						#Certs that may include a "-"
						#Certs that end with a "+"
						#Certs that include at least 2 consecutive uppercase characters
					cert_check = re.findall('[A-Z]+\-+[\w]+|[a-zA-Z]+\+|[\w]+[A-Z]{2,}', sentence)
					
					#Add found certifications to the set of discovered certs in the job listing
					if len(cert_check) > 0:
						#print(IGreen + "[+] Found these certs:")
						#print(cert_check)
						jd_certs.update(cert_check)
					else:
						#print( IRed + "[-] No certs in foundline, iterating")
						#print(IWhite + sentence)
						all_children_by_xpath = jd_foundline.find_elements_by_xpath(".//*")
						
						#Check if any children elements exist that may have certs
						for child in all_children_by_xpath:
							sentence = child.get_attribute('innerHTML')
							cert_check = re.findall('[A-Z]+\-+[\w]+|[a-zA-Z]+\+|[\w]+[A-Z]{2,}', sentence)
							if len(cert_check) > 0:
								#print(IGreen + "[+] Found these certs in child element:")
								#print(cert_check)
								jd_certs.update(cert_check)
							else:
								#print(IRed + "[-] No certs in children")
								pass
								
						tags = ["p", "li", "ul"]
						
						for tag in tags:
							another_el = []
							next_el = jd_foundline.find_elements(By.XPATH, f".//following-sibling::{tag}")
							if len(next_el) > 0:
								sentence = next_el[0].get_attribute('innerHTML')
								#print(IWhite + sentence)
								cert_check = re.findall('[A-Z]+\-+[\w]+|[a-zA-Z]+\+|[\w]+[A-Z]{2,}', sentence)
								if len(cert_check) > 0:
									#print(IGreen + "[+] Found these certs in sibling element:")
									#print(cert_check)
									jd_certs.update(cert_check)
									another_el = next_el[0].find_elements(By.XPATH, f".//following-sibling::{tag}")
									
							#This loop only triggers if we found a single valid cert
							#Cycle through subsequent sibling elements of the same type to find more certifications
							while True:	
									if len(another_el) > 0:
										sentence = another_el[0].get_attribute('innerHTML')
										#print(IWhite + sentence)
										cert_check = re.findall('[A-Z]+\-+[\w]+|[a-zA-Z]+\+|[\w]+[A-Z]{2,}', sentence)
										if len(cert_check) > 0:
											#print(IGreen + "[+] Found these certs in sibling element:")
											#print(cert_check)
											jd_certs.update(cert_check)
											#Try grabbing the next element
											another_el = another_el[0].find_elements(By.XPATH, f".//following-sibling::{tag}")
										#The sibling element didn't have a recognized cert
										else:
											break
									#The next element is absent
									else:
										break
						"""
						next_el = jd_foundline.find_elements(By.XPATH, ".//following-sibling::p")
						print(IWhite + str(len(next_el)))
						next_el = jd_foundline.find_elements(By.XPATH, ".//following-sibling::li")
						print(IWhite + str(len(next_el)))
						next_el = jd_foundline.find_elements(By.XPATH, ".//following-sibling::ul")
						print(IWhite + str(len(next_el)))
						"""
		if (jd_certs == set()):
			no_certs += 1
		else:
			yes_certs += 1
			
		for cert in jd_certs:
			if cert in cert_dic:
				cert_dic[cert] += 1
			else:
				cert_dic[cert] = 1	
		#print(IWhite + str(jd_certs))

	#wd.find_element(By.CLASS_NAME, 'jobs-search__results-list')
	#print(job_id)
	print(IRed + f"[-] A total of {failed_jobs} jobs failed to load while scraping, consider slowing the rate of processing with the -i flag")
	print(IGreen + f"[+] A total of {no_certs} jobs did not have any certs found")
	print(IGreen + f"[+] A total of {yes_certs} jobs did have certs listed")
	
	res = dict(sorted(cert_dic.items(), key=lambda x: (-x[1], x[0])))

	for k,v in res.items():
		print(f"{k} : {v}")
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