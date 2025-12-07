from flask import Flask, render_template, request
from off_client import get_product_by_barcode, search_products

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
    products = []
    selected_product = None

    # default filter vrijednosti
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

    page = 1

    if request.method == "POST":
        action = request.form.get("action", "search")
        page = int(request.form.get("page", "1"))

        # --- pokupi filtere ---
        filters["product"] = request.form.get("product", "").strip()

        def to_float(name):
            val = request.form.get(name)
            if not val:
                return None
            # dozvoli i 20,0 i 20.0
            val = val.replace(",", ".")
            try:
                return float(val)
            except ValueError:
                return None

        filters["sugar"] = to_float("sugar")
        filters["fat"] = to_float("fat")
        filters["energy"] = to_float("energy")
        filters["carbs"] = to_float("carbs")
        filters["protein"] = to_float("protein")

        filters["available_mne"] = bool(request.form.get("available_mne"))
        filters["vegan"] = bool(request.form.get("vegan"))
        filters["lactose_free"] = bool(request.form.get("lactose_free"))
        filters["gluten_free"] = bool(request.form.get("gluten_free"))

        # --- helper za pretragu: vrati max 7 brzo ---
        def run_search(current_page):
            query = filters["product"] or "food"

            try:
                raw = search_products(query, page_size=25, page=current_page)
            except Exception as e:
                print("Greška pri pretrazi proizvoda:", e)
                return []

            filtered = []
            for p in raw:
                nutr = p.get("nutriments", {}) or {}

                def ok_max(key, max_val):
                    """Vrati True ako je vrijednost za key <= max_val ili ako nema limita."""
                    if max_val is None:
                        return True
                    v = nutr.get(key)
                    if v is None:
                        # nema podatka – tretiraj kao da ne prolazi filter
                        return False
                    try:
                        v_float = float(v)
                    except (TypeError, ValueError):
                        return False
                    return v_float <= max_val

                # numerički filteri
                if not ok_max("sugars_100g", filters["sugar"]):
                    continue
                if not ok_max("fat_100g", filters["fat"]):
                    continue
                if not ok_max("energy-kcal_100g", filters["energy"]):
                    continue
                if not ok_max("carbohydrates_100g", filters["carbs"]):
                    continue
                if not ok_max("proteins_100g", filters["protein"]):
                    continue

                # checkbox filteri
                if filters["available_mne"] and "en:montenegro" not in p.get("countries_tags", []):
                    continue
                if filters["vegan"] and "en:vegan" not in p.get("labels_tags", []):
                    continue
                if filters["lactose_free"] and "en:lactose-free" not in p.get("labels_tags", []):
                    continue
                if filters["gluten_free"] and "en:gluten-free" not in p.get("labels_tags", []):
                    continue

                filtered.append(p)
                if len(filtered) >= 7:   # PRVIH 7 I STOP
                    break

            return filtered

        # ========== LOGIKA AKCIJA ==========

        # button Search
        if action == "search":
            page = 1
            products = run_search(page)

        # button Refresh (nova “strana” istih filtera)
        elif action == "refresh":
            page += 1
            products = run_search(page)

        # klik na proizvod – action = "details:<barcode>"
        elif action.startswith("details:"):
            code = action.split(":", 1)[1]
            products = run_search(page)  # da lista postoji za BACK
            try:
                resp = get_product_by_barcode(code)
                selected_product = resp.get("product")
            except Exception as e:
                print("Error fetching product details:", e)

        # dugme Back to list
        elif action == "back":
            products = run_search(page)

    # GET – početno stanje, samo forma bez rezultata
    return render_template(
        "smart_search.html",
        active_page="smart",
        products=products,
        filters=filters,
        page=page,
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
