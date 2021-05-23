# -*- coding: utf-8 -*-
"""
Created on Sun May 23 16:36:33 2021

Main file for scraping options data from online sources for use in analyzing
potenital trades.

@author: Michael Stebbins
"""

from bs4 import BeautifulSoup
import requests

def main():

    # Pull data from Yahoo Finance
    data_url = "https://finance.yahoo.com/quote/SPY/options"
    data_html = requests.get(data_url).content
    print(data_html)

if __name__ == "__main__":
    main()
