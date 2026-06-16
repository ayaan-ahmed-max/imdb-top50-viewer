# imdb-top50-viewer
Python desktop app that scrapes and displays the Top 50 Movies and TV Shows from IMDB. Features a cinema-themed GUI with a welcome screen, scrollable results, ratings, and descriptions. Built with tkinter, Playwright, and BeautifulSoup.

## Setup

```
pip install -r requirements.txt
playwright install chromium
```

IMDB blocks plain HTTP scraping with a bot-detection challenge, so Playwright drives a real (headless) Chromium browser to fetch the page.

## Bugs found in the first draft (and how they were fixed)

The first version of the app got stuck on the loading screen forever and never showed any movies. Here's what was wrong, explained simply:

1. **Typo in the function name.** When you clicked a button, the code tried to run a function called `self._fetch_date` (note: "date", not "data") to go fetch the movie data in the background. But that function didn't actually exist — the real function was named `_fetch_data`. It's like telling someone "go to the _kithen_" when the room is actually called the "kitchen" — they just won't know where to go. Because the name was wrong, the background task crashed immediately, but the crash happened silently (in a background thread), so the screen just sat there showing "Loading..." forever with no error message.

2. **The fetch function was defined in the wrong place.** Even after fixing the typo, the `_fetch_data` function was accidentally written *inside* another function (`load_category`) instead of being its own separate function on the app. In Python, where you indent code changes what it belongs to — a bit like putting a recipe inside a different recipe's instructions instead of giving it its own recipe card. Because of this, `_fetch_data` never actually got attached to the app the way it needed to. It's now been moved out so it's a proper, standalone function the app can call.

3. **The scraper only ever returned 1 result instead of 50.** The line that says "send back the list of movies I found" (`return results`) was indented one level too far, so it was stuck *inside* the loop that goes through each movie one at a time. That meant the code grabbed the very first movie, then immediately said "I'm done, here's my one result" and quit — instead of finishing the loop and handing back all 50. Moving that line outside the loop fixed it.

4. **A small typo meant pages didn't resize properly.** One line used `stick="nsew"` instead of the correct word `sticky="nsew"`. This is a setting that tells a section of the window to stretch and fill the available space. Because of the typo, it was silently ignored (no crash, just didn't do what was intended), so the page content might not resize as nicely as it should. Fixed by correcting the spelling.

5. **IMDB started blocking the scraper entirely.** This wasn't a bug in the code itself — IMDB added bot-detection that blocks simple requests pretending to be a browser. The original code used the `requests` library, which just downloads raw HTML — it can't get past IMDB's check, so it was getting back an empty page with no movies on it at all. The fix was switching to **Playwright**, a tool that controls an actual (invisible/"headless") Chromium browser to load the page like a real person would, which is able to get past the block. As part of this, the part of the code that finds movie titles, years, and ratings on the page also had to be rewritten, because IMDB's website layout had changed since the original scraper was written (genre tags also disappeared from the page entirely, so that field now just shows "N/A").

## Bug found in the second draft (and how it was fixed)

After the first round of fixes, there was no way to go back to the home screen without closing and restarting the app. There actually was a "← Back" button already written in the code — it just wasn't visible. The bar at the top of the results page was set to not resize itself (`pack_propagate(False)`) but was never given an actual height, so it collapsed down to almost nothing and hid the back button inside it. Fixed by giving that top bar a fixed height (`height=60`) so it — and the back button inside it — actually show up on screen.
