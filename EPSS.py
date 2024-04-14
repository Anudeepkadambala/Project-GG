import asyncio
import aiohttp
import pandas as pd
import os

async def fetch(session, base_url, cve):
    url = f"{base_url}{cve}"
    async with session.get(url) as response:
        if response.status == 200:
            return cve, await response.json()
        else:
            print(f"Failed to call API for CVE {cve}. Status code:", response.status)
            return cve, None

async def call_api_with_cve_and_merge(base_url, input_file, output_file):
    try:
        # it will read CVE values from the input CSV file which we will upload and the other empty fields will be blank
        cve_data = pd.read_csv(input_file)
        cve_values = cve_data['CVE'].astype(str).tolist()

        results = {}

        async with aiohttp.ClientSession() as session:
            tasks = [fetch(session, base_url, cve) for cve in cve_values]
            for future in asyncio.as_completed(tasks):
                cve, result = await future
                if result:
                    results[cve] = result['data']

        # this is the meeting point of CSV and CVE and they are togather since then lol
        merged_data = cve_data.merge(pd.DataFrame(results.items(), columns=['CVE', 'data']), on='CVE', how='left')

        
        script_dir = os.path.dirname(os.path.realpath(__file__))

        
        output_file_path = os.path.join(script_dir, output_file)

        
        merged_data.to_csv(output_file_path, index=False)

        print("Merged data exported to", output_file_path)
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    # this is the link to the Hero of the code
    base_url = 'https://api.first.org/data/v1/epss?cve='

    # Give input file path and then sit and relax
    input_file = input("Enter input CSV file path: ")

    # here name the file of your wish with .csv , Thank you for your patience
    output_file = input("Enter output CSV file name (with extension): ")

    asyncio.run(call_api_with_cve_and_merge(base_url, input_file, output_file))
