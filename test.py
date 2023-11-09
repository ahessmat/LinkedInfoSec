import requests
import re

# Replace this URL with the one you want to request
url = "https://www.linkedin.com/jobs/search?currentJobId=3716710886"
url = "https://www.linkedin.com/jobs/view/3719219193"

# Send a GET request to the URL
response = requests.get(url)

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
    word_pattern = re.compile(r"\b(?:[A-Z]{2,}|\w+\+\w+\d+|\w+-\d+)(?![A-Z-])")

    # Iterate through the response content line by line
    for line in response.iter_lines(decode_unicode=True):
        if pattern.search(line):
            matching_words = word_pattern.findall(line)
            if matching_words:
                print("Matching Line:", line)
                print("Matching Words:", matching_words)
                print("TEST: ", set(matching_words))
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
