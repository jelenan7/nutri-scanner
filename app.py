from flask import Flask, render_template, request
from off_client import get_product_by_barcode, search_products
import math

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
        barcode = request.form.get("barcode")
        if barcode:
            try:
                response = get_product_by_barcode(barcode)
                product = response.get("product")

                if not product:
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

    if request.method == "POST":
        action = request.form.get("action", "search")
        page = int(request.form.get("page", 1))

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
        raw = search_products(query, page_size=20, page=1)

        filtered = []
        for p in raw:
            nutr = p.get("nutriments", {}) or {}

            def ok_max(key, max_val):
                if max_val is None:
                    return True
                v = nutr.get(key)
                if v is None:
                    return False
                try:
                    return float(v) <= max_val
                except (TypeError, ValueError):
                    return False

            if not ok_max("sugars_100g", filters["sugar"]): continue
            if not ok_max("fat_100g", filters["fat"]): continue
            if not ok_max("energy-kcal_100g", filters["energy"]): continue
            if not ok_max("carbohydrates_100g", filters["carbs"]): continue
            if not ok_max("proteins_100g", filters["protein"]): continue

            if filters["available_mne"] and "en:montenegro" not in p.get("countries_tags", []): continue
            if filters["vegan"] and "en:vegan" not in p.get("labels_tags", []): continue
            if filters["lactose_free"] and "en:lactose-free" not in p.get("labels_tags", []): continue
            if filters["gluten_free"] and "en:gluten-free" not in p.get("labels_tags", []): continue

            filtered.append(p)

        # 🔹 3️⃣ TOTAL PAGES
        total_pages = max(1, math.ceil(len(filtered) / PER_PAGE))

        # 🔹 4️⃣ REŽI SAMO TRENUTNU STRANICU
        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE
        products = filtered[start:end]

        # details
        if action.startswith("details:"):
            code = action.split(":", 1)[1]
            try:
                resp = get_product_by_barcode(code)
                selected_product = resp.get("product")
            except Exception as e:
                print(e)

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
    print("✅ Pokrećem Flask aplikaciju...")
    app.run(debug=True)
