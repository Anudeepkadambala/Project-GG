
**EPSS.py**

This Python script utilizes asyncio and aiohttp to fetch data asynchronously from an API based on Common Vulnerabilities and Exposures (CVE) identifiers. It then merges this data with an input CSV file and exports the merged data to another CSV file. Let's break down the script:

Async Functions:

fetch: Asynchronously fetches data for a given CVE from the specified API. It constructs the URL using the base URL and CVE identifier, sends a GET request, and returns the CVE identifier along with the JSON response if the request is successful.
call_api_with_cve_and_merge: Reads CVE values from an input CSV file, initiates asynchronous fetch requests for each CVE using aiohttp, waits for all requests to complete, merges the fetched data with the original CSV data based on the CVE identifier, and exports the merged data to a new CSV file.

The fetched data is merged with the original CSV data using the Pandas library. The merge is performed based on the CVE identifier column.
Exporting Merged Data:

The merged data is exported to a new CSV file using the to_csv method of the Pandas DataFrame.

**EPSSV2.py**

It then proceeds to fetch data from a specified API for a list of Common Vulnerabilities and Exposures (CVE) identifiers, merging this data with an input CSV file and exporting the merged data to a new CSV file. 

fetch: Asynchronously fetches data for a given CVE from the specified API.

The script prompts the user to input the path of the source CSV file and specify the name of the output CSV file.
It then calls the call_api_with_cve_and_merge function with the provided input and output file paths using asyncio.run().
