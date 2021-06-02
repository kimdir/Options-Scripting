# -*- coding: utf-8 -*-
"""
Created on Sun May 23 16:36:33 2021

Main file for scraping options data from online sources for use in analyzing
potenital options trades.

@author: Michael Stebbins
"""

from bs4 import BeautifulSoup
import requests
import datetime, time
import csv
import os
from dateutil.relativedelta import relativedelta

weeklies_path = "C:/Users/Kiaru/OneDrive/Financial Tracking/Options Files/Weeklies.csv"
monthlies_path = "C:/Users/Kiaru/OneDrive/Financial Tracking/Options Files/Monthlies.csv"
output_path = "C:/Users/Kiaru/OneDrive/Financial Tracking/Options Files/Options Data.csv"

option_range = 2
expiry_range = 2

def GetTickers():
    weekly_tickers = []
    monthly_tickers = []

    # Get weekly tickers from file
    with open(weeklies_path) as weekly_file:
        tickReader = csv.reader(weekly_file)
        next(tickReader)
        for row in tickReader:
            weekly_tickers.append(row)

    # Get monthly tickers from file
    with open(monthlies_path) as monthly_file:
        tickReader = csv.reader(monthly_file)
        next(tickReader)
        for row in tickReader:
            monthly_tickers.append(row)

    return [weekly_tickers,monthly_tickers]

def GetExpiryDates(count=expiry_range,interval="weekly",weekday="Friday"):
    """
    Retrieves the next count of options expiry dates based on the current date,
    the options interval and what days of the week the options expire.
    """

    expiry_dates=[0 for x in range(0,count)]
    expiry_timestamps=[0 for x in range(0,count)]
    today = datetime.date.today()
    day_of_week = today.weekday()
    friday_index = 4

    if interval.lower() == "weekly":
        if day_of_week > friday_index:
            friday_index += 7

        days_to_expiry = friday_index-day_of_week
        expiry_dates[0] = today + datetime.timedelta(days=days_to_expiry)

        for i in range(1,count):
            expiry_dates[i] = expiry_dates[i-1] + datetime.timedelta(days=7)

    elif interval.lower() == "monthly":
        expiry_dates = [today + relativedelta(months=+i)
                        for i in range(0,count+1)]

        for i in range(len(expiry_dates)):
            earliest_date = datetime.date(expiry_dates[i].year,
                                            expiry_dates[i].month,
                                            15) #Earliest 3rd Friday is the 15th
            expiry_dates[i] = earliest_date.replace(day=(15 + (4 - earliest_date.weekday()) % 7))

        if today > expiry_dates[0]:
            expiry_dates.pop(0)
        else:
            expiry_dates.pop()
    else:
        print("Bad interval")
        return []

    for i in range(len(expiry_dates)):
        expiry_dates[i] = datetime.datetime.combine(expiry_dates[i],datetime.datetime.min.time())
        expiry_timestamps[i] = int(expiry_dates[i].replace(tzinfo=datetime.timezone.utc).timestamp())
    # print(expiry_timestamps)
    return [expiry_dates,expiry_timestamps]

def GetURL(ticker,timestamp):
    """
    Configuration Function

    Assigns the proper URL for the data source selected. URLs will be specific
    to the data source and should be tested before placing in production.
    """

    base_url = "https://finance.yahoo.com/quote/"
    url_suffix = "/options?date="

    full_url = base_url + ticker.upper() + url_suffix + str(timestamp)
    return full_url

def GetOptionInfo(option,ticker,expiry_date):
    option_data = []
    for td in BeautifulSoup(str(option),"html.parser").find_all("td"):
        option_data.append(td.text)

    option_info = {'Contract': option_data[0],
                    'Symbol': ticker,
                    'Strike': option_data[2],
                    'Last': option_data[3],
                    'Bid': option_data[4],
                    'Ask': option_data[5],
                    'Volume': option_data[8],
                    'IV': option_data[10],
                    'Expiry':expiry_date}
    return option_info

def SelectOptions(itm_options,otm_options,option_range):
    selected_options = []
    for i in range(option_range):
        selected_options.append(itm_options[0].pop(-1))
        selected_options.append(itm_options[1].pop(0))
        selected_options.append(otm_options[0].pop(0))
        selected_options.append(otm_options[1].pop(-1))

    return selected_options

def WriteOptionInfo(option_list):
    """
    Takes a list of dictionaries of options information and writes all to a file.
    """

    info_columns = ['Contract','Symbol','Strike','Last','Bid','Ask','Volume','IV','Expiry']

    if os.path.exists(output_path):
        os.remove(output_path)

    with open(output_path,'w',newline='') as out_file:
        writer = csv.DictWriter(out_file,fieldnames = info_columns)
        writer.writeheader()
        for data in option_list:
            writer.writerow(data)

def ScrapeData(ticker,interval):

    # Define expiry dates to examine
    [expiry_dates,expiry_timestamps] = GetExpiryDates()
    selected_options_info = []

    # Iterate through scraping process for each expiry date
    for expiry_index in range(len(expiry_timestamps)):
        time.sleep(2)
        print("Getting data for %s" % (expiry_dates[expiry_index]))

        itm_calls = []
        otm_calls = []
        itm_puts = []
        otm_puts = []
        itm_options = []
        otm_options = []



        # Pull raw HTML data from Yahoo Finance
        data_url = GetURL(ticker,expiry_timestamps[expiry_index])
        data_html = requests.get(data_url).content

        # Isolate table data from raw HTML file
        content = BeautifulSoup(data_html, "html.parser")
        options_tables = []
        tables = content.find_all("table")
        if tables ==[]:
            return
        for i in range(0,len(tables)):
            options_tables.append(tables[i])

        # Sort table data by option type
        calls = options_tables[0].find_all("tr")[1:] # First row is header
        puts = options_tables[1].find_all("tr")[1:]

        # Identify in-the-money and out-of-the-money options
        for call_option in calls:
            if "in-the-money Bgc" in str(call_option):
                itm_calls.append(call_option)
            else:
                otm_calls.append(call_option)

        for put_option in puts:
            if "in-the-money Bgc" in str(put_option):
                itm_puts.append(put_option)
            else:
                otm_puts.append(put_option)

        # Isolate selected range of options
        itm_options = [itm_calls,itm_puts]
        otm_options = [otm_calls,otm_puts]
        selected_option_data = SelectOptions(itm_options,otm_options,option_range)

        # Convert information to .csv output format
        for option in selected_option_data:
            selected_options_info.append(GetOptionInfo(option,ticker,expiry_dates[expiry_index]))

    return selected_options_info

def main():
    """
    Main body of script. Iterates through given watchlists and outputs options
    information within the designated range of the last price of the underlying.
    """

    full_options_list = []
    call_count = 0
    short_limit = 8
    long_limit = 4 * short_limit

    # Pull watchlists and sort by interval
    [weekly_tickers,monthly_tickers] = GetTickers()

    # Iterate through weekly options watchlist
    for symbol in weekly_tickers:
        call_count += 1
        symbol_string =''.join([str(elem) for elem in symbol])
        print("Getting data for %s... Symbol %s/%s" % (symbol_string,call_count,len(weekly_tickers)))
        try:
            symbol_options = ScrapeData(symbol_string,"weekly")
            for option in symbol_options:
                full_options_list.append(option)
        except:
            print("Bad URL, skipping ticker.")
        if call_count%short_limit == 0:
            print(">>> Short call rest")
            time.sleep(60)
        if call_count%long_limit == 0:
            print(">>>>> Long call rest")
            time.sleep(240)


    # Iterate through monthly options watchlist
    for symbol in monthly_tickers:
        symbol_string =''.join([str(elem) for elem in symbol])
        print("Getting data for %s..." % (symbol_string))
        try:
            symbol_options = ScrapeData(symbol_string,"monthly")
            for option in symbol_options:
                full_options_list.append(option)
        except:
            print("Bad URL, skipping ticker.")
        time.sleep(0.5)

    # Output results to .csv file
    WriteOptionInfo(full_options_list)

if __name__ == "__main__":
    main()
