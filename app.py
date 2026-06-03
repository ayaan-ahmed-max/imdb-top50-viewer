import tkinter as tk
from tkinter import ttk, font
import requests
from bs4 import BeautifulSoup
import threading

# CONSTANTS - the things that will not change throughout the code

# the following are the URLs ive used to scrape

URLS = {
    "movies": "https://www.imdb.com/search/title/?title_type=feature&sort=num_votes,desc&count=50",
    "tvshows": "https://www.imdb.com/search/title/?title_type=tv_series&sort=num_votes,desc&count=50",
}

# Browser header i am going to pretend its a real browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# dark colour palette i am going to go for a dark cinema theme
BG_DARK = "#0d0d0d"
BG_DARK = "#0d0d0d"   
BG_CARD = "#1a1a1a"   
BG_HEADER = "#111111"   
GOLD = "#f5c518"   
GOLD_HOVER = "#d4a800"   
TEXT_WHITE = "#ffffff"
TEXT_MUTED = "#aaaaaa"
TEXT_DARK = "#0d0d0d"
ACCENT_BLUE = "#3a7bd5"
RED = "#e74c3c"

# Scrapper Functions

def scrape_imdb(category: str) -> list[dict]:
    """ this will fetch the imdb page for the given category whether it be
        tvshows or movies and wil parse the HTML with BeautifulSoup, and returns
        a list of dictionariess 
        each dictionary should look like this:
         {
            'rank':   '1',
            'title':  'The Shawshank Redemption',
            'year':   '1994',
            'rating': '9.3',
            'genre':  'Drama',
            'desc':   'Two imprisoned men bond...'
        } """
    
    url = URLS[category]
    
    # 1. downloading the webpage html

    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status() #this raises an error if the request failed

    