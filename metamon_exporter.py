#!/usr/bin/python3
from prometheus_client import start_http_server, Summary, Gauge
import random
import time
import requests
import json
import asyncio
import aiohttp

# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
METAMON_PRICE = Gauge('metamon_price', 'Info about METAMON on market', ['id', 'sale_address', 'level'])

# &category=17
# 15 - potions
# 13 - mtm
# 17 - potions
base_url = 'https://market-api.radiocaca.com/nft-sales?pageNo=1&pageSize=20&sortBy=single_price&order=asc&name=&saleType&tokenType&tokenId=-1'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:94.0) Gecko/20100101 Firefox/94.0',
           'Accept': '*/*', 'Accept-Language': 'en-US,en;q=0.5', 'Referer': 'https://market.radiocaca.com/',
           'Origin': 'https://market.radiocaca.com', 'Connection': 'keep-alive', 'Sec-Fetch-Dest': 'empty',
           'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-site', 'TE': 'trailers'}


async def get(url, session):
    try:
        async with session.get(url=url) as response:
            resp = await response.read()
            metamon_info_json = json.loads(resp)
            metamon_level = list(filter(lambda level: level['key'] == 'Level', metamon_info_json['data']['properties']))[0]['value']
            METAMON_PRICE.labels(id=metamon_info_json['data']['id'], sale_address=metamon_info_json['data']['sale_address'], level=metamon_level).set(metamon_info_json['data']['total_price'])
    except Exception as e:
        print("Unable to get url {} due to {}.".format(url, e.__class__))


async def metamon_info(url_list):
    async with aiohttp.ClientSession() as session:
        ret = await asyncio.gather(*[get(url, session) for url in url_list])


def metamon_request(base_url, headers):
    url = base_url + '&category=13'
    metamon_price_response = requests.get(url, headers=headers)
    metamon_price_json = json.loads(metamon_price_response.text)
    url_list = []
    for el in metamon_price_json['list']:
        url_list.append('https://market-api.radiocaca.com/nft-sales/' + str(el['id']))
    asyncio.run(metamon_info(url_list))


if __name__ == '__main__':
    start_http_server(8000)
    while True:
        start = time.time()
        metamon_request(base_url, headers)
        end = time.time()
        print("Took {} seconds to pull 20 websites.".format(end - start))
        time.sleep(5)
