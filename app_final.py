import os
import sys
import folium
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from geopy.geocoders import Nominatim
from random_forest_model_ai_de_folosit import BookingAIPredictor

# === Geolocalizare pentru hartă ===
def get_coords(location):
    geolocator = Nominatim(user_agent="calatorii_app")
    loc = geolocator.geocode(location)
    if loc:
        return loc.latitude, loc.longitude
    return None, None

# === Convertor text în float (cu virgulă) ===
def try_parse_float(value):
    try:
        return float(value.replace(",", "."))
    except:
        return None

# === Generare hartă cu marcatori ===
def genereaza_harta_cazari(localitate, top_cazari):
    lat, lon = get_coords(localitate)
    if not lat:
        return

    m = folium.Map(location=[lat, lon], zoom_start=12)

    # Sortează pentru a atribui poziții (1, 2, 3...)
    sorted_df = top_cazari.sort_values(by="Scor prezis", ascending=False).reset_index(drop=True)

    for idx, row in sorted_df.iterrows():
        numar_pin = idx + 1
        popup_content = f"""
        <b>{row['Nume cazare']}</b><br>
        ⭐ Scor AI: {row['Scor prezis']:.2f}<br>
        ⭐ Număr recenzii: {row['Nr. evaluari']}<br>
        💰 Preț mediu RON: {row['Pret RON']}<br>
        💰 Preț minim RON: {row['Pret minim RON']}<br>
        💰 Preț maxim RON: {row['Pret maxim RON']}<br>
        """
        popup = folium.Popup(popup_content, max_width=350)

        icon = folium.DivIcon(html=f"""
            <div style="font-size:12px;
                        color:white;
                        background-color:{'green' if row['Scor prezis'] >= 9 else 'orange' if row['Scor prezis'] >= 7 else 'red'};
                        border-radius:50%;
                        width:28px;height:28px;
                        text-align:center;
                        line-height:28px;">
                {numar_pin}
            </div>
        """)

        folium.Marker(
            location=[row["Latitudine"], row["Longitudine"]],
            popup=popup,
            tooltip=row["Nume cazare"],
            icon=icon
        ).add_to(m)

    folium.LatLngPopup().add_to(m)
    m.save("harta.html")

# === Interfața principală ===
class TravelApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProofPuff")
        self.setGeometry(100, 100, 900, 800)

        # === Elemente UI
        self.label_loc = QLabel("📍 Localitate:")
        self.input_loc = QLineEdit()
        self.label_topn = QLabel("🔢 Număr cazări:")
        self.input_topn = QLineEdit("5")
        self.input_topn.setFixedWidth(50)
        self.label_comfort = QLabel("🛏️ Comfort minim:")
        self.input_comfort = QLineEdit()
        self.input_comfort.setFixedWidth(50)
        self.label_pret_max = QLabel("💰 Preț maxim RON:")
        self.input_pret_max = QLineEdit()
        self.btn = QPushButton("🔍 Caută și afișează")
        self.btn_reset = QPushButton("🧹 Resetează filtrele")
        self.btn_reset.setFixedWidth(130)
        self.btn_reset.setStyleSheet("font-size: 12px; padding: 4px;")
        self.webview = QWebEngineView()
        self.status = QLabel("")
        self.status.setStyleSheet("font-size: 14pt; font-weight: bold; margin: 10px;")

        self.btn.clicked.connect(self.executa)
        self.btn_reset.clicked.connect(self.reseteaza_formular)

        # === Layouturi
        controls = QHBoxLayout()
        buttons = QHBoxLayout()

        for w in [self.label_loc, self.input_loc, self.label_topn, self.input_topn,
                  self.label_comfort, self.input_comfort, self.label_pret_max, self.input_pret_max,
                  self.btn]:
            controls.addWidget(w)

        buttons.addStretch()               # ↔️ împinge la dreapta
        buttons.addWidget(self.btn_reset)  # 🧹 în dreapta

        layout = QVBoxLayout()
        layout.addWidget(self.webview, stretch=5)
        layout.addLayout(controls, stretch=1)
        layout.addLayout(buttons, stretch=0)
        layout.addWidget(self.status, stretch=0)
        self.setLayout(layout)

        self.model = BookingAIPredictor()
        self.load_initial_map()

    def load_initial_map(self):
        folium.Map(location=[45.9432, 24.9668], zoom_start=6).save("harta.html")
        self.webview.load(QUrl.fromLocalFile(os.path.abspath("harta.html")))

    def executa(self):
        loc = self.input_loc.text().strip()
        top_n = self.input_topn.text().strip()
        comfort_val = try_parse_float(self.input_comfort.text().strip())
        pret_max_val = try_parse_float(self.input_pret_max.text().strip())

        if not loc:
            self.status.setText("⚠️ Introdu o localitate.")
            return
        if not top_n.isdigit():
            self.status.setText("⚠️ Introdu un număr valid.")
            return

        top, mesaj, medie = self.model.top_cazari(
            loc, int(top_n), pret_max=pret_max_val, comfort_min=comfort_val
        )

        if top.empty:
            self.status.setText(mesaj)
            return
        if "Latitudine" not in top or "Longitudine" not in top:
            self.status.setText("⚠️ Lipsesc coordonatele.")
            return

        genereaza_harta_cazari(loc, top)
        self.webview.load(QUrl.fromLocalFile(os.path.abspath("harta.html")))
        self.status.setText(f"{mesaj}\nMedia scor general în {loc.title()}: {medie}")

    def reseteaza_formular(self):
        self.input_comfort.clear()
        self.input_pret_max.clear()
        self.status.setText("🧹 Filtre resetate.")


# === Rulare aplicație ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TravelApp()
    win.show()
    sys.exit(app.exec_())
