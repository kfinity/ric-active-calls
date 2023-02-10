#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2022-01-23

@author: kfinity
"""

import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import math
import time
import os

filename = "data/ric_active_calls.csv"
ac_url = f"https://apps.richmondgov.com/applications/activecalls/Home/ActiveCalls?_={int(time.time())}"


# A quick/dirty function to convert HTML jQuery DataTables to dataframes
def jq_datatables(raw_html, table_id): 
    soup = BeautifulSoup(raw_html, "lxml")
    tab = soup.find(id=table_id)
    columns = [h.text.strip() for h in tab.find_all('th')]
    body = tab.find('tbody')
    data = [[cell.text.strip() for cell in row.find_all('td')] for row in body.find_all('tr')]

    df = pd.DataFrame(data, columns=columns)

    # special cases
    details = body.find_all(attrs={"class": "tblDetailsCell"})
    if len(details) > 0:
        df['Offense Code'] = [d.attrs['data-offensecode'] for d in details]

    return df

r = requests.get(ac_url)
try:
    ac_df = jq_datatables(r.text, 'tblActiveCallsListing')
except Exception as e:
    logging.error(traceback.format_exc())
    exit(1)

# save raw copy
ac_df.to_csv(f"data/ac{time.strftime('%Y%m%d-%H%M%S')}.csv",index=False)

if os.path.isfile(filename):
    db = pd.read_csv(filename)
    db = db.append(ac_df)
else:
    db = ac_df

db.drop_duplicates(inplace=True)

db.to_csv(filename, index=False)

print(f"{db.shape[0]} rows written to {filename}")

