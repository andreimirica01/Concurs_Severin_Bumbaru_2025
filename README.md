# Concurs_Severin_Bumbaru_2025
# ProofPuff: Rating-Based Travel Planning System

This project was developed for the **"Advanced Programming and Artificial Intelligence"** category in Severin Bumbaru 2025 contest. We won the contest with **ProofPuff** , an integrated desktop application designed to help users discover and plan trips (city breaks, shopping breaks, or circuits) based on AI-driven rating predictions and geographic visualization.

---

## 🚀 Project Overview

The system automates the entire pipeline from raw data acquisition to personalized user recommendations:

1. **Web Scraping:** Extracting hotel and accommodation data from Booking.com.


2. **AI Analysis:** Using machine learning to predict ratings and evaluate location quality.


3. **Interactive GUI:** A user-friendly desktop interface for filtering results and viewing them on an interactive map.



---

## 🛠️ Key Features

### 1. Advanced Data Collection

Using `scraper_data_coordonate.py`, the team implemented a robust scraper that:

* Collects over **200 records** with more than **10 characteristics** per entry (e.g., Price, Stars, Cleanliness, Comfort).


* Utilizes **OCR (PaddleOCR)** to extract specific rating categories from images where text might be obfuscated.
* Employs **Undetected Chromedriver** and **ScraperAPI** to bypass anti-bot mechanisms.

### 2. Intelligent Data Processing

* **Data Cleaning:** Techniques to identify errors, remove duplicates, and handle outliers.


* **Supervised Learning:** Features are organized by rating to facilitate AI model training.



### 3. AI Rating Prediction

The application includes an AI solution (e.g., Random Forest) that:

* Trains on the scraped dataset to predict ratings for new locations.
* Evaluates performance using **R² (Coefficient of Determination)** and **Estimation Error**.



### 4. Interactive Visualization

The GUI (`app_final.py`) allows users to:

* Input a location and filter by price or comfort.
* View a **Folium-based map** (integrated into the PyQt5 app) showing top-rated stays with color-coded markers (Green for 9+, Orange for 7+).

---

## 📊 Evaluation Criteria & Compliance

The project was designed to meet the following contest requirements:

| Criterion | Key Aspects | Points |
| --- | --- | --- |
| **Data Collection** | >200 records, >10 characteristics, Web Scraping. | 20p |
| **Data Processing** | Statistical cleaning, duplicate removal, rating-based organization. | 20p |
| **AI Prediction** | Implementation of 2 algorithms, training/testing, R² evaluation. | 30p |
| **Personalized Recommendations** | GUI-based rating suggestions and map integration. | 20p |
| **Presentation** | Originality, PowerPoint presentation, and live GUI demo. | 10p |

---

## 💻 Tech Stack

* **Language:** Python
* **Web Scraping:** Selenium (Undetected Chromedriver), ScraperAPI, BeautifulSoup/Regex.
* **OCR:** PaddleOCR & OpenCV.
* **Data Analysis:** Pandas, NumPy.
* **AI/ML:** Scikit-Learn (Random Forest).
* **GUI:** PyQt5.
* **Mapping:** Folium & Geopy.

---

## 🛠️ Installation & Setup

1. **Clone the repository.**
2. **Install dependencies:**
```bash
pip install PyQt5 PyQtWebEngine folium geopy pandas undetected-chromedriver paddleocr opencv-python

```


3. **Run the Scraper:** Update the `SCRAPER_API_KEY` in `scraper_data_coordonate.py` and run it to populate your dataset.
4. **Launch the App:**
```bash
python app_final.py

```
