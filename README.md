**EPSS.py**

This Python script utilizes asyncio and aiohttp to fetch data asynchronously from an API based on Common Vulnerabilities and Exposures (CVE) identifiers. It then merges this data with an input CSV file and exports the merged data to another CSV file. Let's break down the script:

Async Functions:

fetch: Asynchronously fetches data for a given CVE from the specified API. It constructs the URL using the base URL and CVE identifier, sends a GET request, and returns the CVE identifier along with the JSON response if the request is successful.
call_api_with_cve_and_merge: Reads CVE values from an input CSV file, initiates asynchronous fetch requests for each CVE using aiohttp, waits for all requests to complete, merges the fetched data with the original CSV data based on the CVE identifier, and exports the merged data to a new CSV file.
Main Execution:

The script checks if it's being run as the main module using if __name__ == "__main__".
It prompts the user to input the path of the input CSV file and the desired name for the output CSV file.
It then calls the call_api_with_cve_and_merge function with the provided input and output file paths using asyncio.run().
Exception Handling:

The script includes exception handling within the call_api_with_cve_and_merge function to catch and print any errors that occur during execution.
CSV Data Handling:

The fetched data is merged with the original CSV data using the Pandas library. The merge is performed based on the CVE identifier column.
Exporting Merged Data:

The merged data is exported to a new CSV file using the to_csv method of the Pandas DataFrame.
Output Feedback:

The script prints a message indicating the successful export of the merged data along with the file path.
Overall, this script provides a streamlined way to fetch and merge CVE data from an API with existing data in a CSV file, leveraging asynchronous programming for efficient HTTP requests and Pandas for data manipulation and export.


**EPSSV2.py**

This script automates the installation of required libraries if they are not already installed. It then proceeds to fetch data from a specified API for a list of Common Vulnerabilities and Exposures (CVE) identifiers, merging this data with an input CSV file and exporting the merged data to a new CSV file. Below is a breakdown of its functionalities:

Library Installation:

The script checks if required libraries (aiohttp, pandas, json) are installed. If not, it attempts to install them using pip.
Async Functions:

fetch: Asynchronously fetches data for a given CVE from the specified API.
Main Function:

call_api_with_cve_and_merge: Reads CVE values from an input CSV file. Initiates asynchronous fetch requests for each CVE using aiohttp. Merges the fetched data with the original CSV data. Exports the merged data to a new CSV file.
CSV Data Processing:

The fetched JSON data is parsed and merged with the original CSV data. Each key-value pair in the JSON response becomes a separate column in the CSV file.
Script Execution:

The script prompts the user to input the path of the source CSV file and specify the name of the output CSV file.
It then calls the call_api_with_cve_and_merge function with the provided input and output file paths using asyncio.run().
Error Handling:

The script includes exception handling to catch and print any errors that occur during execution.
This script provides a convenient way to fetch and merge CVE data from an API with existing data in a CSV file, automating the process and making it suitable for use in various data processing pipelines.
