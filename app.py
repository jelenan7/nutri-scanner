from flask import Flask, render_template, request
from off_client import get_product_by_barcode, search_products
import math
import os

app = Flask(__name__)


# ===== HOME =====
@app.route("/")
def home():
    return render_template("home.html", active_page="home")


# ===== BARCODE SCAN PAGE =====
@app.route("/barcode-scan", methods=["GET", "POST"])
def barcode_scan():
    product = None
    not_found = False

    if request.method == "POST":
        barcode = request.form.get("barcode", "").strip()

        if barcode:
            try:
                response = get_product_by_barcode(barcode)

                if response.get("status") == 1:
                    product = response.get("product")
                else:
                    not_found = True

            except Exception as e:
                print("Greška pri dohvaćanju proizvoda:", e)
                not_found = True

    return render_template(
        "barcode_scan.html",
        active_page="barcode",
        product=product,
        not_found=not_found,
    )


# ===== SMART SEARCH PAGE =====
@app.route("/smart-search", methods=["GET", "POST"])
def smart_search():
    PER_PAGE = 7

    products = []
    selected_product = None
    page = 1
    total_pages = 1

    filters = {
        "product": "",
        "sugar": None,
        "fat": None,
        "energy": None,
        "carbs": None,
        "protein": None,
        "available_mne": False,
        "vegan": False,
        "lactose_free": False,
        "gluten_free": False,
    }

    def to_float(name):
        val = request.form.get(name)
        if not val:
            return None
        val = val.replace(",", ".")
        try:
            return float(val)
        except ValueError:
            return None

    def ok_max(nutriments, key, max_val):
        if max_val is None:
            return True

        value = nutriments.get(key)
        if value is None:
            return False

        try:
            return float(value) <= max_val
        except (TypeError, ValueError):
            return False

    if request.method == "POST":
        action = request.form.get("action", "search")

        try:
            page = int(request.form.get("page", 1))
            if page < 1:
                page = 1
        except ValueError:
            page = 1

        # filters
        filters["product"] = request.form.get("product", "").strip()
        filters["sugar"] = to_float("sugar")
        filters["fat"] = to_float("fat")
        filters["energy"] = to_float("energy")
        filters["carbs"] = to_float("carbs")
        filters["protein"] = to_float("protein")

        filters["available_mne"] = bool(request.form.get("available_mne"))
        filters["vegan"] = bool(request.form.get("vegan"))
        filters["lactose_free"] = bool(request.form.get("lactose_free"))
        filters["gluten_free"] = bool(request.form.get("gluten_free"))

        query = filters["product"] or "food"

        try:
            raw = search_products(query, page_size=50, page=1)
        except Exception as e:
            print("Greška pri pretrazi proizvoda:", e)
            raw = []

        filtered = []

        for p in raw:
            nutr = p.get("nutriments", {}) or {}
            labels_tags = p.get("labels_tags", []) or []
            countries_tags = p.get("countries_tags", []) or []

            if not ok_max(nutr, "sugars_100g", filters["sugar"]):
                continue
            if not ok_max(nutr, "fat_100g", filters["fat"]):
                continue
            if not ok_max(nutr, "energy-kcal_100g", filters["energy"]):
                continue
            if not ok_max(nutr, "carbohydrates_100g", filters["carbs"]):
                continue
            if not ok_max(nutr, "proteins_100g", filters["protein"]):
                continue

            if filters["available_mne"] and "en:montenegro" not in countries_tags:
                continue
            if filters["vegan"] and "en:vegan" not in labels_tags:
                continue
            if filters["lactose_free"] and "en:lactose-free" not in labels_tags:
                continue
            if filters["gluten_free"] and "en:gluten-free" not in labels_tags:
                continue

            filtered.append(p)

        total_pages = max(1, math.ceil(len(filtered) / PER_PAGE))

        if page > total_pages:
            page = total_pages

        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE
        products = filtered[start:end]

        if action.startswith("details:"):
            code = action.split(":", 1)[1]
            try:
                resp = get_product_by_barcode(code)
                if resp.get("status") == 1:
                    selected_product = resp.get("product")
            except Exception as e:
                print("Greška pri dohvaćanju detalja proizvoda:", e)

    return render_template(
        "smart_search.html",
        active_page="smart",
        products=products,
        page=page,
        total_pages=total_pages,
        filters=filters,
        selected_product=selected_product,
    )


@app.route("/about")
def about():
    return render_template("about.html", active_page="about")


# ===== HEALTH CHECK =====
@app.route("/ping")
def ping():
    return "Aplikacija radi! ✅"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
