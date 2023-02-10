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
import ssl
import urllib3
import logging

filename = "data/ric_active_calls.csv"
ac_url = f"https://apps.richmondgov.com/applications/activecalls/Home/ActiveCalls?_={int(time.time())}"

# https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled
class CustomHttpAdapter (requests.adapters.HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)

def get_legacy_session():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    return session

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

#r = requests.get(ac_url)
r = get_legacy_session().get(ac_url)
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

