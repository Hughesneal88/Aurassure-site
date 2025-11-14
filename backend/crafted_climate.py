import requests
import pandas
from datetime import datetime, timedelta

def get_cclimate_data(start_date, end_date, api_key, auid):
    header = {
        'Accept': 'text/csv',
        'X-API-KEY': api_key
    }
    url = f"https://cctelemetry-dev.azurewebsites.net/pull-data/{auid}?startDate={start_date}&endDate={end_date}"
    response = requests.get(url, headers=header)
    from io import StringIO
    data = StringIO(response.text)
    df = pandas.read_csv(data)
    return df





# import requests
# import pandas
# from datetime import datetime, timedelta

# url = "https://cctelemetry-dev.azurewebsites.net/pull-data/AU-001-CC1N-01?startDate=2025-07-01&endDate=2025-07-20"
# headers = {'X-API-KEY': 'BNRMAptv53llm9od', 'Accept': 'text/csv'} 
# r = requests.get(url, headers=headers) 
# r.raise_for_status() 
# open('export.csv','wb').write(r.content) 