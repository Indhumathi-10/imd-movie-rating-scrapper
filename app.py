from flask import Flask, render_template, request, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime
import time
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    movies = []
    csv_file = None

    if request.method == "POST":
        imdb_url = request.form.get("imdb_url")

        if not imdb_url.endswith("/"):
            imdb_url += "/"

        # ---------- Selenium Setup ----------
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        driver.get(imdb_url)
        time.sleep(5)

        # Scroll to load all movies
        last_count = 0
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            items = driver.find_elements(By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item")
            if len(items) == last_count:
                break
            last_count = len(items)

        # ---------- Extract Movie Data ----------
        for rank, item in enumerate(items, start=1):
            try:
                title_text = item.find_element(By.CSS_SELECTOR, "h3.ipc-title__text").text
                title = title_text.split(". ", 1)[1] if ". " in title_text else title_text
                movie_url = item.find_element(By.TAG_NAME, "a").get_attribute("href")

                metadata = item.find_elements(By.CSS_SELECTOR, "span.cli-title-metadata-item")
                year = metadata[0].text if metadata else ""

                try:
                    rating = item.find_element(By.CSS_SELECTOR, "span.ipc-rating-star").text.split()[0]
                except:
                    rating = ""

                movies.append([rank, title, year, rating, movie_url])
            except:
                continue

        driver.quit()

        # ---------- Save CSV ----------
        if movies:
            df = pd.DataFrame(
                movies,
                columns=["Rank", "Title", "Year", "IMDb Rating", "URL"]
            )

            csv_file = f"imdb_movies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(csv_file, index=False, encoding="utf-8-sig")

    return render_template("index.html", movies=movies, csv_file=csv_file)


@app.route("/download/<path:filename>")
def download_file(filename):
    return send_file(filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=8000)