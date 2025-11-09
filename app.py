# APP.py
import os
import base64
import asyncio
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html as st_html

# ---- OFF client import (radi i ako se fajl zove client_off.py) ----
try:
    from off_client import get_product, search_products, extract_image_url  # type: ignore
except Exception:
    from client_off import get_product, search_products, extract_image_url  # type: ignore


# =============================
# Helpers (logo / background)
# =============================
def _first_existing(paths: List[str]) -> Optional[str]:
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def _as_data_uri(path: Optional[str]) -> Optional[str]:
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    ext = os.path.splitext(path)[1].lower().replace(".", "") or "png"
    return f"data:image/{ext};base64,{b64}"

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")

LOGO_PATH = _first_existing([
    "assets/nutri-logo.png", "assets/logo.png", "assets/nutri-score.png",
    os.path.join(DESKTOP, "nutri-logo.png"),
    os.path.join(DESKTOP, "logo.png"),
    os.path.join(DESKTOP, "nutri-score.png"),
])
LOGO_URI = _as_data_uri(LOGO_PATH)

def _find_intro_bg() -> Optional[str]:
    asset = _first_existing([
        "assets/intro-bg.png", "assets/intro-bg.jpg",
        "assets/background.png", "assets/background.jpg",
        "assets/nutri-bg.png", "assets/nutri-bg.jpg",
    ])
    if asset:
        return asset
    if os.path.isdir(DESKTOP):
        imgs = [os.path.join(DESKTOP, f) for f in os.listdir(DESKTOP)
                if os.path.splitext(f)[1].lower() in {".png", ".jpg", ".jpeg", ".webp"}]
        if imgs:
            imgs.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return imgs[0]
    return None

INTRO_BG_PATH = _find_intro_bg()
INTRO_BG_URI = _as_data_uri(INTRO_BG_PATH)


# =============================
# Page setup
# =============================
st.set_page_config(
    page_title="Nutri-scanner",
    page_icon=(LOGO_PATH if LOGO_PATH else "🍋"),
    layout="wide"
)

# ---- Theme & FX (Citrus & Teal + futuristicki detalji) ----
CSS = """
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --primary:#0F766E; --primary-hov:#115E59;
  --secondary:#22C55E; --accent:#F59E0B;
  --info:#0891B2; --success:#16A34A; --warning:#F59E0B; --error:#EF4444;
  --surface:#FFFFFF; --subsurface:#F8FAFC;
  --ink:#0F172A; --muted:#64748B; --border:#E2E8F0;
}

/* base */
html, body, [class*="css"]{
  background:
    radial-gradient(900px 400px at 12% -8%, rgba(34,197,94,.10), transparent 60%),
    radial-gradient(900px 400px at 90% -8%, rgba(8,145,178,.10), transparent 60%),
    var(--subsurface)!important;
  color: var(--ink);
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

/* sticky topbar */
.topbar{
  display:flex; align-items:center; justify-content:space-between; gap:16px;
  background:rgba(255,255,255,.82); backdrop-filter: blur(10px);
  border:1px solid var(--border); border-radius:14px; padding:10px 14px;
  box-shadow:0 10px 30px rgba(2,8,23,.10);
  position:sticky; top:0; z-index:9999;
}
.brand{ display:flex; align-items:center; gap:.65rem; }
.brand .logo{ width:32px; height:32px; border-radius:8px; border:1px solid var(--border); }
.brand .title{ font-family:'Poppins',system-ui; font-weight:700; font-size:1.2rem; letter-spacing:.2px; }

/* nav buttons */
.navrow{ display:flex; gap:.6rem; align-items:center; }
.navbtn{
  display:inline-flex; align-items:center; gap:.5rem; padding:.55rem 1.0rem;
  background:linear-gradient(180deg, var(--primary), #0d6a63);
  color:#fff; font-weight:700; border:none; border-radius:12px; cursor:pointer;
  box-shadow:0 6px 16px rgba(15,118,110,.25); transition: transform .15s ease, box-shadow .2s ease;
}
.navbtn:hover{ transform: translateY(-1px); box-shadow:0 10px 24px rgba(15,118,110,.35); }
.navbtn.secondary{
  background:transparent; color:var(--primary); border:1px solid var(--primary);
  box-shadow:none;
}
.app-subtle{ color:var(--muted); }

/* cards & grid */
.card{
  background:rgba(255,255,255,.9); backdrop-filter: blur(6px);
  border:1px solid var(--border); border-radius:16px; padding:16px;
  box-shadow:0 10px 30px rgba(2,8,23,.08); transition: transform .15s ease, box-shadow .2s ease, border-color .2s ease;
}
.card:hover{ transform: translateY(-2px); box-shadow:0 16px 40px rgba(2,8,23,.12); border-color:#d7e2ee; }
.grid{ display:grid; grid-template-columns:repeat(auto-fill, minmax(520px, 1fr)); gap:16px; }

/* result card */
.card-horizontal{ display:flex; gap:16px; align-items:flex-start; }
.card-horizontal .thumb{ width:150px; flex:0 0 150px; }
.card-horizontal .thumb img{ width:100%; height:auto; border-radius:12px; border:1px solid var(--border); }
.card-horizontal .info{ flex:1; min-width:0; }
.meta-row{ display:flex; gap:.5rem; flex-wrap:wrap; margin:.35rem 0 .1rem 0; }
.kpis{ display:flex; gap:12px; color:#475467; font-size:.9rem; margin-top:.2rem; }

/* chips/badges */
.chip{
  display:inline-flex; align-items:center; gap:.35rem;
  padding:.28rem .6rem; border-radius:999px; font-size:.85rem; font-weight:600;
  background:#E2F8EE; color:#065F46; border:1px solid #A7F3D0;
}

/* NUTRI-SCORE scale */
.ns{ display:inline-flex; align-items:center; gap:.5rem; }
.ns .label{ font-weight:800; color:#334155; letter-spacing:.3px; }
.ns-scale{ display:grid; grid-template-columns:repeat(5, 28px); gap:3px; align-items:center; }
.ns-seg{ width:28px; height:18px; border-radius:5px; opacity:.35; box-shadow: inset 0 0 0 1px rgba(0,0,0,.08); transition: transform .18s ease, opacity .18s ease, filter .18s ease; }
.ns-a{ background:#2E7D32; }      /* A */
.ns-b{ background:#66BB6A; }      /* B */
.ns-c{ background:#FACC15; }      /* C */
.ns-d{ background:#FB8C00; }      /* D */
.ns-e{ background:#EF4444; }      /* E */
.ns-seg.active{ opacity:1; transform: translateY(-2px) scale(1.05); filter: drop-shadow(0 2px 6px rgba(0,0,0,.2)); }
.ns-big{ font-weight:900; font-size:.95rem; margin-left:.2rem; }
.ns-big.a{ color:#2E7D32; } .ns-big.b{ color:#66BB6A; } .ns-big.c{ color:#B45309; }
.ns-big.d{ color:#C2410C; } .ns-big.e{ color:#EF4444; }

/* details key:value */
.kv1{ display:block; margin-top:.5rem; }
.kv1 .row{ padding:6px 0; border-bottom:1px dashed var(--border); }
.kv1 .row:last-child{ border-bottom:none; }
.kv1 .k1{ color:#475467; font-weight:600; margin-right:6px; }
.kv1 .v1{ color:#0F172A; font-weight:600; }

/* buttons inside Streamlit */
.stButton > button{
  border-radius:10px; font-weight:700;
  background:var(--primary); border:1px solid var(--primary); color:#fff;
}
.stButton > button:hover{ background:var(--primary-hov); border-color:var(--primary-hov); }

/* inputs */
.stTextInput > div > div > input, .stNumberInput input, .stMultiSelect, .stSelectbox, .stCheckbox{
  background:var(--surface);
}

/* sticky filter bar under topbar */
.stickybar{ position: sticky; top: 72px; z-index: 500; background: rgba(255,255,255,.90); backdrop-filter: blur(6px); padding: 8px 8px 2px 8px; border-radius: 12px; border:1px solid var(--border); box-shadow:0 6px 16px rgba(2,8,23,.08); }

/* mobile */
@media (max-width: 700px){
  .grid{ grid-template-columns:1fr; }
  .card-horizontal{ flex-direction:column; }
  .card-horizontal .thumb{ width:100%; }
}
</style>
"""
st_html(CSS, height=0)


# =============================
# Cache & API helpers
# =============================
@st.cache_data(ttl=3600, show_spinner=False)
def cached_product(barcode: str) -> Dict[str, Any]:
    return asyncio.run(get_product(barcode))

@st.cache_data(ttl=600, show_spinner=False)
def cached_search(params: Dict[str, Any]) -> Dict[str, Any]:
    return asyncio.run(
        safe_search(
            category_en=params.get("category_en"),
            vegan=params.get("vegan", False),
            max_sugars_100g=params.get("max_sugars_100g"),
            nutri_grades=params.get("nutri_grades"),
            only_cg=params.get("only_cg", False),
            page_size=params.get("page_size", 24),
            page=params.get("page", 1),
            sort_by=params.get("sort_by", "unique_scans_n"),
        )
    )

async def safe_search(**kwargs):
    try:
        return await asyncio.wait_for(search_products(**kwargs), timeout=15.0)
    except asyncio.TimeoutError:
        raise httpx.ReadTimeout("Local timeout (15s)")

def cg_flag(product: Dict[str, Any]) -> str:
    tags = product.get("countries_tags")
    if isinstance(tags, list) and tags:
        norm = [t.split(":")[-1].strip().lower() for t in tags]
    else:
        countries = (product.get("countries") or "")
        norm = [c.strip().lower() for c in countries.split(",") if c.strip()]
    if not norm: return "?"
    return "YES" if "montenegro" in norm else "NO"

# --- NEW: Nutri-Score as a colored scale like the official banner ---
def nutriscore_scale(grade: Optional[str]) -> str:
    letters = "abcde"
    g = (grade or "").strip().lower()
    active = letters.index(g) if g in letters else -1
    segs = []
    for i, ch in enumerate(letters):
        cls = f"ns-seg ns-{ch}" + (" active" if i == active else "")
        segs.append(f"<div class='{cls}' title='{ch.upper()}'></div>")
    big_cls = f"ns-big {g if g in letters else ''}"
    big_txt = (grade or "N/A").upper()
    return f"<span class='ns'><span class='label'>Nutri-Score</span><span class='ns-scale'>{''.join(segs)}</span><span class='{big_cls}'>{big_txt}</span></span>"

# Keep NOVA gradient badge
def nova_badge(nova: Optional[int]) -> str:
    return f"<span class='chip' style='background:linear-gradient(135deg,#0891B2,#22C55E); color:#fff; border:0;'>NOVA {nova if nova else '?'}</span>"

def format_details(product: Dict[str, Any]) -> str:
    name = product.get("product_name") or "—"
    brand = product.get("brands") or "—"
    code = product.get("code") or "—"
    grade = (product.get("nutrition_grades") or "N/A").upper()
    nova = product.get("nova_group") or "?"
    nutr = product.get("nutriments") or {}
    def num(key: str) -> str:
        v = nutr.get(key)
        if isinstance(v, (int, float)): return f"{v:.1f}"
        try: return f"{float(str(v).replace(',', '.')):.1f}"
        except Exception: return "—"
    sugars = num("sugars_100g"); energy = num("energy-kcal_100g")
    fat = num("fat_100g"); sat_fat = num("saturated-fat_100g"); salt = num("salt_100g")
    tags = product.get("countries_tags") or []
    countries = ", ".join(t.split(":")[-1].title() for t in tags) or "—"
    avail = cg_flag(product)

    rows = [
        ("Product", name), ("Brand", brand), ("Barcode", code),
        ("Nutri-Score", grade), ("NOVA group", str(nova)),
        ("Energy (kcal/100g)", energy), ("Sugars (g/100g)", sugars),
        ("Fat (g/100g)", fat), ("Saturated fat (g/100g)", sat_fat),
        ("Available in ME", avail),
    ]
    html = ["<div class='kv1'>"]
    for k, v in rows:
        html.append(f"<div class='row'><span class='k1'>{k}:</span> <span class='v1'>{v}</span></div>")
    html.append(f"<div class='app-subtle' style='margin-top:.35rem'>Countries (OFF): {countries}</div>")
    html.append("</div>")
    return "\n".join(html)


# =============================
# Top bar (logo + nav)
# =============================
def topbar(active: str):
    st.markdown("<div class='topbar'>", unsafe_allow_html=True)
    left, right = st.columns([0.5, 0.5])

    with left:
        if LOGO_URI:
            st.markdown(
                f"<div class='brand'><img class='logo' src='{LOGO_URI}' alt='logo'/><div class='title'>Nutri-scanner</div></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown("<div class='brand'><div class='title'>Nutri-scanner</div></div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='navrow'>", unsafe_allow_html=True)
        a,b,c = st.columns(3)
        with a:
            if st.button("Home", use_container_width=True, type=("primary" if active=="intro" else "secondary")):
                st.query_params.update(page="intro")
        with b:
            if st.button("Scan", use_container_width=True, type=("primary" if active=="home" else "secondary")):
                st.query_params.update(page="home")
        with c:
            if st.button("Smart search", use_container_width=True, type=("primary" if active=="search" else "secondary")):
                st.query_params.update(page="search")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.write("")


# =============================
# Sidebar: cache
# =============================
with st.sidebar:
    st.subheader("Cache")
    st.caption("Search cached 10 min; product 60 min.")
    if st.button("Clear cache"):
        st.cache_data.clear(); st.cache_resource.clear()
        st.success("Cache cleared.")


# =============================
# Router: intro / scan / search
# =============================
page = st.query_params.get("page", "intro")
topbar("home" if page == "home" else ("search" if page == "search" else "intro"))

# ---------- INTRO ----------
if page == "intro":
    # Per-page background image (20% opacity ≈ 80% transparency)
    if INTRO_BG_URI:
        st_html(f"""
        <style>
        .intro-hero::before {{
          content: "";
          position: absolute; inset: -16px;
          background-image: url('{INTRO_BG_URI}');
          background-size: cover; background-position: center;
          opacity: .2; border-radius: 16px; pointer-events:none;
          filter: saturate(1) contrast(1.05);
        }}
        </style>
        """, height=0)

    st.markdown(
        """
        <div class="card intro-hero" style="padding:28px; position:relative; overflow:hidden;">
          <div style="
            position:absolute; inset:-40px -40px auto auto; width:340px; height:340px;
            background: conic-gradient(from 180deg, #22C55E22, #0F766E22, #F59E0B22, #22C55E22);
            filter: blur(30px); border-radius: 50%;
          "></div>
          <h2 style="font-family:Poppins,system-ui; margin:0 0 .4rem 0;">Smarter nutrition, in one scan.</h2>
          <p class="app-subtle" style="margin:.2rem 0 1rem 0;">
            Scan a barcode and instantly see Nutri-Score, sugars and ingredients. Discover healthier alternatives without the guesswork.
          </p>
          <div style="display:flex; gap:.6rem; flex-wrap:wrap;">
            <a href="?page=home" class="navbtn" style="text-decoration:none;">Start scanning</a>
            <a href="?page=search" class="navbtn secondary" style="text-decoration:none;">Try Smart search</a>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2 = st.columns([0.55, 0.45])
    with c1:
        st.markdown(
            """
            <div class="card">
              <h4 style="margin-top:0;">What you can do</h4>
              <ul>
                <li><b>Scan</b> a barcode (EAN-13) to get product image, brand, Nutri-Score, NOVA group, allergens and nutrients.</li>
                <li><b>Smart search</b> by category, vegan label, <i>max sugars g/100g</i>, Nutri-Score (A–E) and availability in ME.</li>
                <li>Fast, clean cards with color-coded badges and a concise <i>Details</i> section.</li>
              </ul>
              <p class="app-subtle" style="margin:0.4rem 0 0">Data source: Open Food Facts (open data).</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="card" style="text-align:center">
              <div style="font-weight:700; margin-bottom:.6rem">Nutri-Score scale</div>
              <div>{nutriscore_scale('a')}</div>
              <div style="margin-top:.4rem">{nutriscore_scale('c')}</div>
              <div style="margin-top:.4rem">{nutriscore_scale('e')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------- SCAN ----------
elif page == "home":
    st.markdown("#### Scan a barcode")
    barcode = st.text_input("Enter barcode (EAN-13)", placeholder="e.g. 3017624010701")
    if st.button("Scan"):
        st.session_state["do_scan"] = True

    if st.session_state.get("do_scan") and (barcode or "").strip():
        try:
            with st.spinner("Fetching product…"):
                product = cached_product(barcode.strip())

            img_url = extract_image_url(product)
            name = product.get("product_name", "Unknown product")
            brand = product.get("brands") or "—"
            grade = product.get("nutrition_grades")
            nova  = product.get("nova_group")
            allergens = product.get("allergens") or "—"
            nutr = product.get("nutriments") or {}

            st.write("---")
            left, right = st.columns([0.35, 0.65])

            with left:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                if img_url: st.image(img_url, use_column_width=True)
                else: st.markdown("<div class='app-subtle'>No image available</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with right:
                st.markdown(
                    f"""
                    <div class="card">
                      <div style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;">
                        <div style="font-weight:800;font-size:1.05rem">{name}</div>
                        <span class="chip">{brand}</span>
                      </div>
                      <div class="meta-row">
                        {nutriscore_scale(grade)} {nova_badge(nova)}
                      </div>
                      <div class="app-subtle">Allergens: {allergens}</div>
                      {format_details(product)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                rows: List[Dict[str, Any]] = []
                for key, label in [
                    ("energy-kcal_100g", "Energy (kcal/100g)"),
                    ("fat_100g", "Fat (g/100g)"),
                    ("saturated-fat_100g", "Saturated fat (g/100g)"),
                    ("sugars_100g", "Sugars (g/100g)"),
                    ("salt_100g", "Salt (g/100g)"),
                    ("proteins_100g", "Protein (g/100g)"),
                ]:
                    val = (nutr or {}).get(key)
                    if val is not None:
                        try: rows.append({"Nutrient": label, "Value": float(str(val).replace(",", "."))})
                        except Exception: rows.append({"Nutrient": label, "Value": val})
                if rows:
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)

        except httpx.ReadTimeout:
            st.warning("The API is slow and the request timed out. Please try again.")
        except Exception as e:
            st.error(f"Error: {e}")

# ---------- SMART SEARCH ----------
else:
    st.markdown("#### Smart search")
    # Sticky filter bar
    st.markdown("<div class='stickybar'>", unsafe_allow_html=True)
    with st.container():
        f1, f2, f3, f4, f5 = st.columns([2, 1, 1, 1, 1])
        with f1:
            category = st.text_input("Category (EN)", value="chocolates", placeholder="e.g. chocolates / biscuits / yogurts")
        with f2:
            vegan = st.checkbox("Vegan only", value=False)
        with f3:
            max_sugar = st.number_input("Max sugars g/100g", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
        with f4:
            nutri_pick = st.multiselect("Nutri-Score", ["A", "B", "C", "D", "E"])
        with f5:
            only_cg = st.checkbox("Available in ME", value=False)

        b1, b2, _ = st.columns([0.15, 0.15, 0.7])
        with b1:
            search_clicked = st.button("Search")
        with b2:
            load_more_clicked = st.button("Load more")
    st.markdown("</div>", unsafe_allow_html=True)

    if "search_page" not in st.session_state:
        st.session_state["search_page"] = 1
    if search_clicked:
        st.session_state["search_page"] = 1

    if search_clicked or load_more_clicked:
        if load_more_clicked:
            st.session_state["search_page"] += 1

        try:
            with st.spinner("Searching Open Food Facts…"):
                params = {
                    "category_en": category.strip() or None,
                    "vegan": vegan,
                    "max_sugars_100g": max_sugar,
                    "nutri_grades": [g.lower() for g in nutri_pick] if nutri_pick else None,
                    "only_cg": only_cg,
                    "page_size": 24,
                    "page": st.session_state["search_page"],
                    "sort_by": "unique_scans_n",
                }
                data = cached_search(params)

            products = data.get("products", []) or []

            def sugar_ok(p: Dict[str, Any], limit: float) -> bool:
                v = (p.get("nutriments") or {}).get("sugars_100g", None)
                if v is None: return False
                try:
                    return float(str(v).replace(",", ".")) <= float(limit)
                except Exception:
                    return False

            if max_sugar is not None:
                products = [p for p in products if sugar_ok(p, max_sugar)]

            total = int(data.get("count", len(products)))
            if not products and st.session_state["search_page"] == 1:
                st.info("No results for the selected filters.")
            else:
                st.caption(f"Page {st.session_state['search_page']} • ~{total} products found")
                st.markdown("<div class='grid'>", unsafe_allow_html=True)

                for p in products:
                    img = extract_image_url(p)
                    name = p.get("product_name") or "Unnamed"
                    brand = p.get("brands") or "—"
                    grade = p.get("nutrition_grades")
                    nova  = p.get("nova_group")
                    sugars = (p.get("nutriments") or {}).get("sugars_100g")
                    energy = (p.get("nutriments") or {}).get("energy-kcal_100g")
                    me = cg_flag(p)

                    st.markdown("<div class='card card-horizontal'>", unsafe_allow_html=True)
                    if img:
                        st.markdown(f"<div class='thumb'><img src='{img}' alt='product image'/></div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='thumb'><div class='app-subtle'>No image</div></div>", unsafe_allow_html=True)

                    st.markdown(
                        f"""
                        <div class='info'>
                          <div style='display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;'>
                            <div style='font-weight:800'>{name}</div>
                            <span class='chip'>{brand}</span>
                          </div>
                          <div class='meta-row'>
                            {nutriscore_scale(grade)} {nova_badge(nova)}
                          </div>
                          <div class='kpis'>
                            <div>🍭 Sugars: <b>{('-' if sugars is None else sugars)}</b> g/100g</div>
                            <div>🔥 Energy: <b>{('-' if energy is None else energy)}</b> kcal/100g</div>
                          </div>
                          <div class='meta-row' style='margin-top:.2rem;'>
                            <span class='chip'>Available in ME: {me}</span>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

                    with st.expander("Details"):
                        st.markdown(format_details(p), unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

        except httpx.ReadTimeout:
            st.warning("Search is taking too long. Please try again or narrow your filters.")
        except Exception as e:
            st.error(f"Error while searching: {e}")
