import subprocess
import sys
import os

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required_packages = ["shodan", "pandas"]

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        install(package)

import shodan
import pandas as pd

SHODAN_API_KEY = "2bkjIJvPmBailFOwRqvbrNjSGp1cRtG9"
api = shodan.Shodan(SHODAN_API_KEY)

search_query = input("Enter the search query for Shodan: ")
output_file = input("Enter the output CSV file name (with .csv extension): ")

if not output_file.endswith('.csv'):
    output_file += '.csv'


current_dir = os.path.dirname(os.path.abspath(__file__))
output_file_path = os.path.join(current_dir, output_file)

try:

    results = api.search(search_query)
    
 
    if not results['matches']:
        print("No results found for the given search query.")
        sys.exit()

    
    data = []
    for result in results['matches']:
        item = {
            'IP': result.get('ip_str', ''),
            'Port': result.get('port', ''),
            'Hostnames': result.get('hostnames', []),
            'Location': result.get('location', {}),
            'ISP': result.get('isp', ''),
            'Organization': result.get('org', ''),
            'Operating System': result.get('os', ''),
            'Timestamp': result.get('timestamp', ''),
            'Data': result.get('data', '')
        }
        data.append(item)

    
    df = pd.DataFrame(data)

    
    if not df.empty:
        location_df = pd.json_normalize(df['Location'])
        df = pd.concat([df.drop(columns='Location'), location_df], axis=1)

    
    df.to_csv(output_file_path, index=False)
    print(f"Data successfully exported to {output_file_path}")

except shodan.APIError as e:
    print(f"Error: {e}")
