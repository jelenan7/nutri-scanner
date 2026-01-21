# Nutri Scanner  
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)]()
[![Flask](https://img.shields.io/badge/Flask-Framework-black.svg)]()
[![API](https://img.shields.io/badge/OpenFoodFacts-API-green.svg)]()
[![License](https://img.shields.io/badge/Data-ODbL-lightgrey.svg)]()

Nutri Scanner is a lightweight Flask application for scanning product barcodes or searching food items using the **Open Food Facts API**.  
It supports real-time camera scanning, nutritional filtering, and clean responsive UI templates.

---

## ⚙️ Features
- Barcode scanning using `html5-qrcode` (camera or file upload)
- Manual search with filters:
  - sugar, fat, carbs, protein, calories
  - vegan, lactose-free, gluten-free
  - available in Montenegro
- Product detail preview with images and nutritional breakdown
- Responsive templated UI with Flask + Jinja2
- Green flash UX effect on successful scan

---

## 📁 Project Structure

nutri-scanner/
├── app.py
├── off_client.py
├── requirements.txt
├── README.md
├── .gitignore
├── static/
│   ├── style.css
│   ├── gif/
│   └── png/
└── templates/
    ├── base.html
    ├── home.html
    ├── about.html
    ├── barcode_scan.html
    ├── smart_search.html
    └── pagination.j2


---

## 📦 Requirements
requirements.txt


---

## 🧹 Recommended .gitignore


---

## 🌐 Deployment

The project can be deployed easily on **Render** or **Railway**.

### Render Deployment
1. Create a new **Web Service**
2. Connect your GitHub repo  
3. Set:

Your app will be available at a public URL automatically.

---

## 🔌 API Usage

Nutri Scanner communicates with:

- `/api/v0/product/<barcode>.json`  
- `/cgi/search.pl` (query & filters)

API helpers are implemented in **off_client.py**.

---

## 📜 License & Attribution

Data provided by **Open Food Facts**, licensed under the **Open Database License (ODbL)**.  
Nutritional values may vary by region; always verify product packaging for medical or allergy concerns.

---

## 👤 Author

**Jelena Nikčević**  
Master’s student in Artificial Intelligence  
Email: **nikcevicj7@gmail.com**

