import tkinter as tk
from tkinter import ttk, font
import requests
from bs4 import BeautifulSoup
import threading

# CONSTANTS - the things that will not change throughout the code

# the following are the URLs ive used to scrape

URL = {
    "movies": "https://www.imdb.com/search/title/?title_type=feature&sort=num_votes,desc&count=50",
    "tvshows": "https://www.imdb.com/search/title/?title_type=tv_series&sort=num_votes,desc&count=50",
}

