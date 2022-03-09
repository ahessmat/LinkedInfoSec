Command for processing your _allinfo.csv file

awk -F "'" '{for (i=1; i<=NF; i+=2) $i=""} 1' pentester_allinfo.csv | tr '\n' '\0' > pentester_certs.txt
