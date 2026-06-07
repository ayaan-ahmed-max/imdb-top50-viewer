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

    # 2. parsing the html using beautifulsoup, beautiful soup will turn the raw html into a searchable tree

    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    rank = 1

    # 3. finding every movie/show container on the page
    #       IMDB wraps each item in a <dv class="lister-item mode-advanced"> this can be seen on the inspect of the page

    items = soup.find_all("div", class_="lister-item mode-advanced")  # this basically just tells the library to just get all of the date from the div

    for item in items:
        # Extracting the div - the text part

        content = item.find("div", class_="lister-item-content")
        if not content:
            continue        # just means that if theres nun there just keep going

        # ---title---
        title_tag = content.find("h3", class_="lister-item-header")
        title = title_tag.find("a").text.strip() if title_tag else "Unknown"

        # ---year---
        year_tag = title_tag.find("span", class_="lister-item-year") if title_tag else None
        year = year_tag.text.strip("() ") if year_tag else "N/A"

        # sometimes the year on the web looks like "(2019-)" for ongoing tvshows so i am just going to clean it
        year = year.replace("-", "-").strip()

        # ---rating---
        rating_tag = content.find("strong")
        rating = rating_tag.text.strip() if rating_tag else "N/A"

        # ---genre---
        genre_tag = content.find("span", class_="genre")
        genre = genre_tag.text.strip() if genre_tag else "N/A"

        # ---description--- (this was a bit hard)
        # the description is inside <p class="text-muted"> tags
        # the first one is the certificate/runtime line - skipping that one
        # the second one is the actual description
        p_tags = content.find_all("p", class_="text-muted")
        desc = p_tags[1].text.strip() if len(p_tags) > 1 else "No description available."

        results.append({
            "rank": str(rank),
            "title": title,
            "year": year,
            "rating": rating,
            "genre":  genre,
            "desc":   desc,
        })    
        rank += 1

        return results
    


    # GUI APPLICATION CLASS -> THE MAIN COURSE ALSO THE HARDEST PART OF THIS

    class IMDBApp(tk.Tk):

        """ in this class i will create all the pages/frames """

        def __init__(self):
            super().__init__()  # thsi calls the tk.Tk's init to set up the window big brain move

            #--window setup--
            self.title("IMDB Top 50 Viewer")
            self.geometry("950x680")
            self.minsize(800, 600)
            self.configure(bg=BG_DARK)
            self.resizable(True, True)

            # --shared data storage--
            # this dictionary will hold scraped results so i dont have to rescrape on every single visit

            self.data = {"movies": None, "tvshows": None}

            # --build fonts--
            self._setup_fonts()

            # --build for all pages--
            # all pages will share the same grid cell (row=0, col=0)
            # so stacking them with tkraise() works

            container = tk.Frame(self, bg=BG_DARK)
            container.pack(fill="both", expand=True)
            container.grid_rowconfigure(0, weight=1)
            container.grid_columnconfigure(0, weight=1)

            self.frames = {}

            for PageClass in (WelcomePage, ResultsPage):
                frame = PageClass(parent=container, controller=self)
                self.frames[PageClass.__name__] = frame
                frame.grid(row=0, column=0, stick="nsew")

            # --show welcome screen first--
            self.show_frame("WelcomePage")

        
        def _setup_fonts(self):
            """Define font objects used across the whole app."""
            self.font_title   = font.Font(family="Georgia",    size=32, weight="bold")
            self.font_sub     = font.Font(family="Helvetica",  size=13)
            self.font_btn     = font.Font(family="Helvetica",  size=14, weight="bold")
            self.font_heading = font.Font(family="Georgia",    size=18, weight="bold")
            self.font_item    = font.Font(family="Helvetica",  size=12, weight="bold")
            self.font_small   = font.Font(family="Helvetica",  size=10)
            self.font_desc    = font.Font(family="Helvetica",  size=10)

        def show_frame(self, name: str):
            """Bring the named frame to the front"""
            self.frames[name].tkraise()

        def load_category(self, category: str):
            """ this function is called when the user picks movies
            or tv shows 
            it then switches to the results page and kicks off background scraping 
            'category' is either movies or tvshows """
            results_page = self.frames["ResultsPage"]
            results_page.set_category(category)
            self.show_frame("ResultsPage")

            if self.data[category] is not None:         # if the category has already been scraped so it just shows it
                results_page.display_results(self.data[category])
                return
            
            # otherwise it scrapes in a background thread, so this helps the GUI stays responsive

            results_page.show_loading()
            thread = threading.Thread(
                target=self._fetch_date,
                args=(category,),
                daemon=True  # daemon=True means that the thread automatically closes/dies if the app closes
            )

            thread.start()
            