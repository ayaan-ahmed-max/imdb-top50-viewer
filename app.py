import tkinter as tk
from tkinter import ttk, font
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
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

    # 1. downloading the rendered page with a real (headless) browser
    #       plain requests gets blocked by IMDB's bot-detection (AWS WAF challenge),
    #       so we use playwright/chromium which behaves like a real browser

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=HEADERS["User-Agent"])
        page.goto(url, timeout=30000)
        page.wait_for_selector("li.ipc-metadata-list-summary-item", timeout=15000)
        # the first 25 items render almost immediately, but the rest stream in
        # a moment later, so we wait until all 50 are actually in the DOM
        page.wait_for_function(
            "document.querySelectorAll('li.ipc-metadata-list-summary-item').length >= 50",
            timeout=15000,
        )
        html = page.content()
        browser.close()

    # 2. parsing the html using beautifulsoup, beautiful soup will turn the raw html into a searchable tree

    soup = BeautifulSoup(html, "html.parser")

    results = []

    # 3. finding every movie/show container on the page
    #       IMDB's current search results wrap each item in <li class="ipc-metadata-list-summary-item">

    items = soup.select("li.ipc-metadata-list-summary-item")

    for rank, item in enumerate(items, start=1):
        # ---title--- (comes prefixed with "1. ", "2. " etc so we strip that off)
        title_tag = item.select_one("h3.ipc-title__text") or item.select_one("h4.ipc-title__text")
        raw_title = title_tag.get_text(strip=True) if title_tag else "Unknown"
        title = re.sub(r"^\d+\.\s*", "", raw_title)

        # ---year--- (first item in the metadata list - year, runtime, certificate)
        meta_items = item.select("div.dli-title-metadata li.ipc-inline-list__item")
        year = meta_items[0].get_text(strip=True) if meta_items else "N/A"

        # ---rating---
        rating_tag = item.select_one("span.ipc-rating-star--rating")
        rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"

        # ---genre--- no longer shown on the search results card, IMDB removed it
        genre = "N/A"

        # ---description---
        desc_tag = item.select_one("div.ipc-html-content-inner-div")
        desc = desc_tag.get_text(strip=True) if desc_tag else "No description available."

        results.append({
            "rank": str(rank),
            "title": title,
            "year": year,
            "rating": rating,
            "genre":  genre,
            "desc":   desc,
        })

    return results



    # GUI APPLICATION CLASS -> THE MAIN COURSE ALSO THE HARDEST PART OF THIS
class IMDBApp(tk.Tk):

        """ in this class i will create all the pages/frames """

        def __init__(self):
            super().__init__()  # thsi calls the tk.Tk's init to set up the window big brain move

            #--window setup--
            self.title("IMDB Top 50 Vfiewer")
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
                frame.grid(row=0, column=0, sticky="nsew")

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
                target=self._fetch_data,
                args=(category,),
                daemon=True  # daemon=True means that the thread automatically closes/dies if the app closes
            )

            thread.start()

        def _fetch_data(self, category: str):
            """ what this does is that it runs in a background thread
            fetches data, stores it, then schedules GUI update on the main thread

            *p.s VERY IMPORTANT TO KNOW THAT TKINTER IS NOT THREAD-SAFE GUI widgets cannot be updated
            directly from a thread, thus we use self.after(0, callback) to schedule updates on the
            main thread safely """

            try:

                items = scrape_imdb(category)
                self.data[category] = items

                # .Schedule GUI update on main thread
                self.after(0, lambda: self.frames["ResultsPage"].display_results(items))

            except Exception as e:
                error_msg = f"Failed to load data.\n\nError: {str(e)}"
                self.after(0, lambda: self.frames["ResultsPage"].show_error(error_msg))

# PAGE 1 -- WELCOME SCREEN
class WelcomePage(tk.Frame):
    """
    The first screen the user sees.
    Contains the title, a short tagline, and two options buttons.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_DARK)
        self.controller = controller
        self._build()

    def _build(self):

        # -- vertical centering trick :))
        """
        this puts empty rows with weight on top and bottom
        and pushes the real content in the middle"""

        self.rowconfigure(0, weight=1)   # top spacer
        self.rowconfigure(1, weight=0)   # content
        self.rowconfigure(2, weight=1)   # bottom spacer
        self.columnconfigure(0, weight=1)

        # content wrapper
        wrapper = tk.Frame(self, bg=BG_DARK)
        wrapper.grid(row=1, column=0)

        # IMDB typa style gold accent bar at the top
        accent = tk.Frame(self, bg=GOLD, height=4)
        accent.place(relx=0, rely=0, relwidth=1)

        # star icon (using unicode)
        tk.Label(
            wrapper, text="*", font=("Georgia", 48),
            bg=BG_DARK, fg=GOLD
        ).pack(pady=(0, 8))

        # app title
        tk.Label(
            wrapper,
            text="IMDB TOP 50",
            font=self.controller.font_title,
            bg=BG_DARK,
            fg=TEXT_WHITE,
        ).pack()

        # tagline
        tk.Label(
            wrapper,
            text="Discover the highest-rated movies and tv shows",
            font=self.controller.font_sub,
            bg=BG_DARK,
            fg=TEXT_MUTED
        ).pack(pady=(6, 40))

        # buttons row
        btn_frame = tk.Frame(wrapper, bg=BG_DARK)
        btn_frame.pack()

        self._make_button(
            btn_frame,
            label="🎬  Top 50 Movies",
            category="movies",
            side="left",
        )
        
        tk.Frame(btn_frame, bg=BG_DARK, width=24).pack(side="left") # this is the spacer

        self._make_button(
            btn_frame,
            label="📺  Top 50 TV Shows",
            category="tvshows",
            side="left",
        )

        # footer
        tk.Label(
            self,
            text="Data sourced from IMDB - Built with Python and tkinter",

            font=self.controller.font_small,
            bg=BG_DARK,
            fg="#555555",
        ).place(relx=0.5, rely=0.97, anchor="s")

    def _make_button(self, parent, label, category, side):
        """This creates a styled sorta button that will basically just call the 
        load_category function when it is clicked"""

        btn = tk.Label(
            parent,
            text=label,
            font=self.controller.font_btn,
            bg=GOLD,
            fg=TEXT_DARK,
            padx=28,
            pady=14,
            cursor="hand2",
            relief="flat",
        )
        btn.pack(side=side)

        # also adding some hover effects i.e changing colour when the mouse enters or leaves
        btn.bind("<Enter>", lambda e: btn.configure(bg=GOLD_HOVER))
        btn.bind("<Leave>", lambda e: btn.configure(bg=GOLD))
        btn.bind("<Button-1>", lambda e: self.controller.load_category(category))


# PAGE 2 -- RESULTS SCREEN

class ResultsPage(tk.Frame):
    """ 
    Displays thte list of top 50 movies or tvshows
    
    layout:
    TOP BAR with a back button and title 
    SCROLLABLE LIST of movie cards """

    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_DARK)
        self.controller = controller
        self.category = "movies"
        self._build()

    def _build(self):
        # --top bar--
        self.topbar = tk.Frame(self, bg=BG_DARK, height=60)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)     # this doesnt shrink it to fit children

        # back button
        back_btn = tk.Label(
            self.topbar,
            text="← Back",
            font=self.controller.font_btn,
            bg=BG_HEADER,
            fg=GOLD,
            padx=16,
            cursor="hand2",
        )

        back_btn.pack(side="left", fill="y")
        back_btn.bind("<Button-1>", lambda e: self.controller.show_frame("WelcomePage"))
        back_btn.bind("<Enter>", lambda e: back_btn.configure(fg=GOLD_HOVER))
        back_btn.bind("<Leave>", lambda e: back_btn.configure(fg=GOLD))

        # page title (updated dynamically)
        self.title_label = tk.Label(
            self.topbar,
            text="",
            font=self.controller.font_heading,
            bg=BG_HEADER,
            fg=TEXT_WHITE,
        )
        self.title_label.pack(side="left", padx=8)

        # count badge
        self.count_label = tk.Label(
            self.topbar,
            text="",
            font=self.controller.font_small,
            bg=GOLD,
            fg=TEXT_DARK,
            padx=8,
            pady=3,
        )
        self.count_label.pack(side="left", padx=8)

        # gold separator line under top bar
        tk.Frame(self, bg=GOLD, height=2).pack(fill="x")

        # scrollable area setup
        # tkinter doesnt have a native scrollbar frame sooo the trick here is to use
        # canvas scrollbar and the frame inside the canvas
        scroll_area = tk.Frame(self, bg=BG_DARK)
        scroll_area.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(scroll_area, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            scroll_area, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        # This inner frame is what we actually put widgets inside
        self.inner = tk.Frame(self.canvas, bg=BG_DARK)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.inner, anchor="nw"
        )
 
        # Bind events to keep scroll region updated
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
 
        # Mouse wheel scrolling — bind to the whole app
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)   # Linux scroll up
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)   # Linux scroll down
 
    def _on_inner_configure(self, event):
        """Called when the inner frame changes size — updates the scroll region."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
 
    def _on_canvas_configure(self, event):
        """Called when the canvas is resized — makes inner frame match canvas width."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
 
    def _on_mousewheel(self, event):
        """Handles mouse wheel scrolling cross-platform."""
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
 
    def set_category(self, category: str):
        """Update the page title based on the chosen category."""
        self.category = category
        if category == "movies":
            self.title_label.configure(text="Top 50 Movies")
        else:
            self.title_label.configure(text="Top 50 TV Shows")
        self.count_label.configure(text="")
 
    def _clear_inner(self):
        """this remove all widgets from the scrollable area."""
        for widget in self.inner.winfo_children():
            widget.destroy()
        # Reset scroll position to top
        self.canvas.yview_moveto(0)
 
    def show_loading(self):
        """this shows a loading spinner message while data is being fetched."""
        self._clear_inner()
        tk.Label(
            self.inner,
            text="⏳  Loading data from IMDB...",
            font=self.controller.font_heading,
            bg=BG_DARK,
            fg=TEXT_MUTED,
        ).pack(pady=120)
 
    def show_error(self, message: str):
        """Show an error message if scraping fails."""
        self._clear_inner()
        tk.Label(
            self.inner,
            text="⚠️  Error",
            font=self.controller.font_heading,
            bg=BG_DARK,
            fg=RED,
        ).pack(pady=(80, 8))
        tk.Label(
            self.inner,
            text=message,
            font=self.controller.font_sub,
            bg=BG_DARK,
            fg=TEXT_MUTED,
            wraplength=500,
            justify="center",
        ).pack()
 
    def display_results(self, items: list[dict]):
        """
        this renders the full list of movie/TV show cards.
        and it is called after scraping finishes (from the main thread).
        """
        self._clear_inner()
        self.count_label.configure(text=f"{len(items)} titles")
 
        # Outer padding frame
        pad = tk.Frame(self.inner, bg=BG_DARK)
        pad.pack(fill="x", padx=20, pady=12)
 
        for item in items:
            self._make_card(pad, item)
 
    def _make_card(self, parent, item: dict):
        """
        Builds one card row for a single movie/show.
 
        Visual layout of each card:
        
         [rank]  TITLE (year)                    ★ rating    
                 Genre chips                                 
                 Description text...                          
        """
        # ── Card frame ──
        card = tk.Frame(
            parent,
            bg=BG_CARD,
            pady=10,
            padx=14,
        )
        card.pack(fill="x", pady=4)
 
        # ── Left column: rank number ──
        rank_label = tk.Label(
            card,
            text=item["rank"],
            font=font.Font(family="Georgia", size=20, weight="bold"),
            bg=BG_CARD,
            fg=GOLD,
            width=3,
            anchor="n",
        )
        rank_label.pack(side="left", anchor="nw", padx=(0, 10), pady=(2, 0))
 
        # ── Right column: all the details ──
        details = tk.Frame(card, bg=BG_CARD)
        details.pack(side="left", fill="x", expand=True)
 
        # Title row: TITLE (year) ── [spacer] ── ★ rating
        title_row = tk.Frame(details, bg=BG_CARD)
        title_row.pack(fill="x")
 
        tk.Label(
            title_row,
            text=f"{item['title']}  ({item['year']})",
            font=self.controller.font_item,
            bg=BG_CARD,
            fg=TEXT_WHITE,
            anchor="w",
        ).pack(side="left")
 
        if item["rating"] != "N/A":
            tk.Label(
                title_row,
                text=f"★  {item['rating']}",
                font=font.Font(family="Helvetica", size=11, weight="bold"),
                bg=GOLD,
                fg=TEXT_DARK,
                padx=8,
                pady=1,
            ).pack(side="right")
 
        # Genre chips
        if item["genre"] and item["genre"] != "N/A":
            genre_row = tk.Frame(details, bg=BG_CARD)
            genre_row.pack(fill="x", pady=(4, 0))
            for g in item["genre"].split(","):
                tk.Label(
                    genre_row,
                    text=g.strip(),
                    font=self.controller.font_small,
                    bg="#2a2a2a",
                    fg=TEXT_MUTED,
                    padx=6,
                    pady=2,
                ).pack(side="left", padx=(0, 4))
 
        # Description
        desc = item["desc"]
        if len(desc) > 160:
            desc = desc[:160].rstrip() + "…"
        tk.Label(
            details,
            text=desc,
            font=self.controller.font_desc,
            bg=BG_CARD,
            fg=TEXT_MUTED,
            wraplength=700,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(5, 0))
 
        # Subtle bottom border
        tk.Frame(parent, bg="#2a2a2a", height=1).pack(fill="x")
 
 
#  ENTRY POINT
if __name__ == "__main__":
    app = IMDBApp()
    app.mainloop()   # starts the tkinter event loop — the app now waits for user input