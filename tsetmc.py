import requests as req
import pandas as pd
import datetime
import calendar
import jdatetime as jd
import numpy as np
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
import arabic_reshaper as ar
from scipy.optimize import curve_fit
import time
"""
    _Description_
"""
def stock_history(symbol: str = None,
                  inscode: int = None, 
                  days: int = 0,
                  start_date: str =  None,
                  end_date: str = None
                  ):
    """
    This function retrieves the historical stock data, either by symbol or inscode, and returns it as a DataFrame.

    Args:
        symbol (str): The symbol of the stock. You can find the symbol on tsetmc.com.
        inscode (int): The inscode of the stock. You can find the inscode on tsetmc.com.
        days (int): The number of days of historical data to retrieve. Default is 0, which returns all available history. If you have entered the number of days, do not enter the start date and end date.
        start_date (str): The start date for retrieving historical stock data. Should be provided in the "YYYY-MM-DD" format as a string. If not specified, the default is the earliest available date in the historical data.
        end_date (str): The end date for retrieving historical stock data. Should be provided in the "YYYY-MM-DD" format as a string. If not specified, the default is the latest available date in the historical data.

    Returns:
        pd.DataFrame: DataFrame containing historical stock data.
        
    Raises:
        ValueError: If inscode is not a 16 or 17 digit integer.
        Exception: If any other error occurs during the data retrieval process.

    Examples:
        symbol = "فملی"
        inscode = 35425587644337450
        start_date = "2021-01-01"
        end_date = "2022-01-01"
        inscode = 99999999999999999  # Invalid inscode (18 digits)
        symbol = "لبینای" # Invalid symbol. The symbol was not found.
    """
    try:
        # Set the user agent for the request headers
        headers = {"User-Agent" : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}

        # If inscode is provided, fetch data using inscode
        if inscode is not None:
            if not (isinstance(inscode, int) and (len(str(inscode)) == 16 or len(str(inscode)) == 17)):
                raise ValueError(f"Invalid inscode: {inscode}. Inscode should be a 16 or 17 digit integer.")
            
            # Construct the URL for fetching historical data by inscode
            url = f'http://cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyList/{inscode}/{days}'
            
            # Try to send the GET request, retrying in case of errors
            for _ in range(3):
                try:
                    response = req.request("GET", url, headers=headers)
                    response.raise_for_status()  # Raise an error for bad responses
                    break  # If successful, exit the loop
                except req.RequestException as e:
                    print(f"Error sending request: {e}")
                    time.sleep(5)  # Sleep for 5 seconds before retrying

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Parse the JSON response
                output_json = response.json()
                # Normalize the JSON and create a DataFrame
                df = pd.DataFrame(output_json['closingPriceDaily'])

                # Drop unnecessary columns
                df.drop(columns=["qTotTran5J", "priceChange","priceMin", "priceMax", "zTotTran", "pDrCotVal",  "last", "insCode", "id", "iClose", "yClose", "hEven"], inplace=True)

                # Convert the 'date' column to datetime format
                df["dEven"] = pd.to_datetime(df["dEven"], format='%Y%m%d')
                df.insert(loc=0, column="date_shamsi", value =list(map(lambda x : jd.date.fromgregorian(
                                                                                    year=int(str(x)[:4]), 
                                                                                    month=int(str(x)[5:7]), 
                                                                                    day=int(str(x)[8:10])), df["dEven"])))
                # # Rename columns for better clarity
                df = df.rename(columns={"dEven": "date",
                                        "pClosing": "close", 
                                        "qTotCap": "value_of_trade"})

                df = df.set_index(df["date"], drop=True)
                if start_date is None:
                    start_date = df.index.min()
                elif end_date is None:
                    end_date = df.index.max()
                else:
                    start_date = pd.to_datetime(start_date, format="%Y-%m-%d").date()
                    end_date = pd.to_datetime(end_date, format="%Y-%m-%d").date()  
                # Filter the dataframe based on start_date and end_date
                df = df[start_date : end_date]

                return df

            else:
                # If the request was not successful, raise an exception with the status code
                raise Exception(f"Failed to get data. Status code: {response.status_code}")

        # If symbol is provided, find inscode and recursively call the function
        elif symbol is not None:
            # Construct the URL for fetching instrument search data by symbol
            url = f"https://cdn.tsetmc.com/api/Instrument/GetInstrumentSearch/{symbol}"
            # Try to send the GET request, retrying in case of errors
            for _ in range(3):
                try:
                    resp = req.get(url=url, headers=headers)
                    resp.raise_for_status()  # Raise an error for bad responses
                    break  # If successful, exit the loop
                except req.RequestException as e:
                    print(f"Error sending request: {e}")
                    time.sleep(5)  # Sleep for 5 seconds before retrying

            # Parse the JSON response
            df = pd.DataFrame(resp.json())
            ins = next((df.iloc[i]["instrumentSearch"]["insCode"] for i in range(len(df)) if len(df.iloc[i]["instrumentSearch"]["lVal18AFC"]) == len(symbol)), None)

            # If inscode is found, recursively call the function with inscode
            if ins is not None:
                return stock_history(inscode=ins, days=days, start_date=start_date, end_date=end_date)
            else:
                # If inscode is not found, raise an exception
                raise Exception(f"Inscode not found for symbol: {symbol}")

        # If neither symbol nor inscode is provided, return a descriptive message
        else:
            return "No valid parameters provided for fetching stock data."

    except ValueError as ve:
        print(f"ValueError: {ve}")
    except req.RequestException as re:
        print(f"RequestException: {re}")
    except Exception as e:
        print(f"Error: {e}")
