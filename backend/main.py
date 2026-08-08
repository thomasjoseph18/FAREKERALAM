import os
from datetime import date

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client, Client


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
UPDATE_TOKEN = os.getenv("FUEL_UPDATE_TOKEN")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Fare Keralam API",
    description="Kerala fare and operating-cost calculation API",
    version="1.1.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SUPABASE
# ============================================================

supabase: Client | None = None

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )


def require_database():
    if supabase is None:
        raise HTTPException(
            status_code=500,
            detail="Database is not configured"
        )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "Fare Keralam API",
        "status": "online",
        "version": "1.1.0"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "database_configured": supabase is not None
    }


# ============================================================
# VEHICLES
# ============================================================

@app.get("/api/vehicles")
def get_vehicles():
    require_database()

    try:
        response = (
            supabase
            .table("vehicles")
            .select("*")
            .eq("active", True)
            .execute()
        )

        return {
            "success": True,
            "count": len(response.data),
            "vehicles": response.data
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# VEHICLE CATEGORIES
# ============================================================

@app.get("/api/categories")
def get_categories():
    require_database()

    try:
        response = (
            supabase
            .table("vehicle_categories")
            .select("*")
            .eq("active", True)
            .order("id")
            .execute()
        )

        return {
            "success": True,
            "count": len(response.data),
            "categories": response.data
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# ENERGY SOURCES
# ============================================================

@app.get("/api/energy-sources")
def get_energy_sources():
    require_database()

    try:
        response = (
            supabase
            .table("energy_sources")
            .select("*")
            .eq("active", True)
            .order("id")
            .execute()
        )

        return {
            "success": True,
            "count": len(response.data),
            "energy_sources": response.data
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# PRICES
# ============================================================

@app.get("/api/prices")
def get_prices(
    energy_source: str | None = Query(default=None),
    location: str = Query(default="Kerala")
):
    require_database()

    try:
        query = (
            supabase
            .table("price_history")
            .select("*")
            .eq("location", location)
            .order("price_date", desc=True)
        )

        if energy_source:
            energy_response = (
                supabase
                .table("energy_sources")
                .select("id")
                .eq("name", energy_source)
                .limit(1)
                .execute()
            )

            if not energy_response.data:
                raise HTTPException(
                    status_code=404,
                    detail="Energy source not found"
                )

            energy_id = energy_response.data[0]["id"]

            query = query.eq(
                "energy_source_id",
                energy_id
            )

        response = query.execute()

        return {
            "success": True,
            "count": len(response.data),
            "prices": response.data
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# LATEST PRICES
# ============================================================

@app.get("/api/latest-prices")
def get_latest_prices(
    location: str = Query(default="Kerala")
):
    require_database()

    try:
        response = (
            supabase
            .table("price_history")
            .select("*")
            .eq("location", location)
            .order("price_date", desc=True)
            .limit(100)
            .execute()
        )

        latest = {}

        for item in response.data:

            key = (
                item.get("energy_source_id"),
                item.get("district")
            )

            if key not in latest:
                latest[key] = item

        prices = list(latest.values())

        return {
            "success": True,
            "count": len(prices),
            "location": location,
            "prices": prices
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# DATA SOURCES
# ============================================================

@app.get("/api/sources")
def get_sources():
    require_database()

    try:
        response = (
            supabase
            .table("data_sources")
            .select("*")
            .order("id")
            .execute()
        )

        return {
            "success": True,
            "count": len(response.data),
            "sources": response.data
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# SOURCE STATUS
# ============================================================

@app.get("/api/source-status")
def get_source_status():
    require_database()

    try:
        response = (
            supabase
            .table("data_sources")
            .select(
                "id,name,organization,url,"
                "verification_status,last_checked_at,"
                "last_successful_update_at,"
                "automatic_update_supported"
            )
            .order("id")
            .execute()
        )

        return {
            "success": True,
            "sources": response.data
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# FARE RULES
# ============================================================

@app.get("/api/fare-rules")
def get_fare_rules():
    require_database()

    try:
        response = (
            supabase
            .table("fare_rules")
            .select("*")
            .eq("status", "active")
            .order("effective_from", desc=True)
            .execute()
        )

        return {
            "success": True,
            "count": len(response.data),
            "fare_rules": response.data
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# FARE SLABS
# ============================================================

@app.get("/api/fare-slabs")
def get_fare_slabs(
    fare_rule_id: int | None = Query(default=None)
):
    require_database()

    try:
        query = (
            supabase
            .table("fare_slabs")
            .select("*")
            .order("from_km")
        )

        if fare_rule_id is not None:
            query = query.eq(
                "fare_rule_id",
                fare_rule_id
            )

        response = query.execute()

        return {
            "success": True,
            "count": len(response.data),
            "fare_slabs": response.data
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# COST DATA
# ============================================================

@app.get("/api/costs")
def get_costs(
    category: str | None = Query(default=None),
    location: str = Query(default="Kerala")
):
    require_database()

    try:
        query = (
            supabase
            .table("cost_data")
            .select("*")
            .eq("location", location)
            .order("effective_date", desc=True)
        )

        if category:

            category_response = (
                supabase
                .table("cost_categories")
                .select("id")
                .eq("name", category)
                .limit(1)
                .execute()
            )

            if not category_response.data:
                raise HTTPException(
                    status_code=404,
                    detail="Cost category not found"
                )

            category_id = category_response.data[0]["id"]

            query = query.eq(
                "cost_category_id",
                category_id
            )

        response = query.execute()

        return {
            "success": True,
            "count": len(response.data),
            "costs": response.data
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# DATA STATUS
# ============================================================

@app.get("/api/data-status")
def data_status():
    require_database()

    try:

        vehicles = (
            supabase
            .table("vehicles")
            .select("id", count="exact")
            .eq("active", True)
            .execute()
        )

        prices = (
            supabase
            .table("price_history")
            .select("id", count="exact")
            .execute()
        )

        fare_rules = (
            supabase
            .table("fare_rules")
            .select("id", count="exact")
            .execute()
        )

        return {
            "success": True,
            "today": str(date.today()),
            "active_vehicles": vehicles.count or 0,
            "price_records": prices.count or 0,
            "fare_rules": fare_rules.count or 0
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# FUEL PRICE UPDATE
# ============================================================

class FuelPriceUpdate(BaseModel):

    fuel: str = Field(
        ...,
        description="Petrol or Diesel"
    )

    price: float = Field(
        ...,
        gt=0
    )

    location: str = "Kerala"

    district: str | None = None

    price_date: date | None = None

    source_reference: str


@app.post("/api/admin/update-fuel-price")
def update_fuel_price(
    data: FuelPriceUpdate,
    token: str = Query(...)
):
    """
    Insert a verified petrol/diesel price
    into price_history.

    Requires FUEL_UPDATE_TOKEN.
    """

    require_database()

    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------

    if not UPDATE_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="FUEL_UPDATE_TOKEN is not configured"
        )

    if token != UPDATE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid update token"
        )

    # --------------------------------------------------------
    # VALIDATE FUEL
    # --------------------------------------------------------

    fuel_name = data.fuel.strip().title()

    if fuel_name not in [
        "Petrol",
        "Diesel"
    ]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only Petrol and Diesel "
                "are supported currently"
            )
        )

    # --------------------------------------------------------
    # FIND ENERGY SOURCE
    # --------------------------------------------------------

    energy_response = (
        supabase
        .table("energy_sources")
        .select("id,name,unit")
        .eq("name", fuel_name)
        .limit(1)
        .execute()
    )

    if not energy_response.data:
        raise HTTPException(
            status_code=404,
            detail=(
                f"{fuel_name} energy source "
                "not found"
            )
        )

    energy_source = energy_response.data[0]

    # --------------------------------------------------------
    # FIND COST CATEGORY
    # --------------------------------------------------------

    category_response = (
        supabase
        .table("cost_categories")
        .select("id,name")
        .eq("name", fuel_name)
        .limit(1)
        .execute()
    )

    if not category_response.data:
        raise HTTPException(
            status_code=404,
            detail=(
                f"{fuel_name} cost category "
                "not found"
            )
        )

    cost_category = category_response.data[0]

    # --------------------------------------------------------
    # FIND PPAC SOURCE
    # --------------------------------------------------------

    source_response = (
        supabase
        .table("data_sources")
        .select("id,name,url")
        .eq(
            "name",
            "PPAC Petrol and Diesel RSP"
        )
        .limit(1)
        .execute()
    )

    if not source_response.data:
        raise HTTPException(
            status_code=404,
            detail="PPAC data source not found"
        )

    source_id = source_response.data[0]["id"]

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    effective_date = (
        data.price_date
        or date.today()
    )

    # --------------------------------------------------------
    # DUPLICATE CHECK
    # --------------------------------------------------------

    existing_query = (
        supabase
        .table("price_history")
        .select("id,value")
        .eq(
            "cost_category_id",
            cost_category["id"]
        )
        .eq(
            "energy_source_id",
            energy_source["id"]
        )
        .eq(
            "location",
            data.location
        )
        .eq(
            "price_date",
            str(effective_date)
        )
    )

    if data.district is None:

        existing_query = existing_query.is_(
            "district",
            "null"
        )

    else:

        existing_query = existing_query.eq(
            "district",
            data.district
        )

    existing = (
        existing_query
        .limit(1)
        .execute()
    )

    if existing.data:

        return {
            "success": True,
            "status": "unchanged",
            "message": (
                "A price record already exists "
                "for this fuel, location and date"
            ),
            "record": existing.data[0]
        }

    # --------------------------------------------------------
    # INSERT PRICE
    # --------------------------------------------------------

    record = {

        "cost_category_id":
            cost_category["id"],

        "energy_source_id":
            energy_source["id"],

        "value":
            data.price,

        "unit":
            energy_source["unit"],

        "location":
            data.location,

        "district":
            data.district,

        "price_date":
            str(effective_date),

        "source_id":
            source_id,

        "source_reference":
            data.source_reference,

        "retrieved_at":
            str(date.today())
    }

    try:

        response = (
            supabase
            .table("price_history")
            .insert(record)
            .execute()
        )

        return {

            "success": True,

            "status": "changed",

            "message": (
                f"{fuel_name} price "
                "stored successfully"
            ),

            "record": (
                response.data[0]
                if response.data
                else record
            )
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# PPAC SOURCE
# ============================================================

PPAC_URL = (
    "https://ppac.gov.in/"
    "retail-selling-price-rsp-of-petrol-diesel-and-domestic-lpg/"
    "price-build-up-of-petrol-and-diesel"
)


# ============================================================
# PPAC CONNECTION TEST
# ============================================================

@app.get("/api/admin/test-ppac")
def test_ppac(
    token: str = Query(...)
):
    """
    Read-only test of the official PPAC page.
    Does NOT write to the database.
    """

    if not UPDATE_TOKEN:
        raise HTTPException(
            status_code=500,
            detail=(
                "FUEL_UPDATE_TOKEN "
                "is not configured"
            )
        )

    if token != UPDATE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid update token"
        )

    try:

        response = requests.get(
            PPAC_URL,
            timeout=30,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Fare Keralam official data updater)"
                ),
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml,"
                    "application/xml;q=0.9,"
                    "*/*;q=0.8"
                ),
                "Accept-Language": (
                    "en-IN,en;q=0.9"
                )
            }
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        tables = soup.find_all("table")

        page_text = soup.get_text(
            " ",
            strip=True
        )

        return {

            "success": True,

            "status_code":
                response.status_code,

            "final_url":
                response.url,

            "page_title": (
                soup.title.get_text(
                    strip=True
                )
                if soup.title
                else None
            ),

            "table_count":
                len(tables),

            "page_size":
                len(response.text),

            "contains_petrol":
                "Petrol" in page_text,

            "contains_diesel":
                "Diesel" in page_text,

            "contains_kerala":
                "Kerala" in page_text
        }

    except requests.RequestException as error:

        raise HTTPException(
            status_code=502,
            detail=(
                f"PPAC request failed: "
                f"{str(error)}"
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# PPAC STRUCTURE DIAGNOSTIC
# ============================================================

@app.get("/api/admin/inspect-ppac")
def inspect_ppac(
    token: str = Query(...)
):
    """
    Read-only PPAC diagnostic.

    This endpoint examines the page structure
    so we can build the automatic extractor safely.

    Does NOT write to the database.
    """

    if not UPDATE_TOKEN:
        raise HTTPException(
            status_code=500,
            detail=(
                "FUEL_UPDATE_TOKEN "
                "is not configured"
            )
        )

    if token != UPDATE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid update token"
        )

    try:

        response = requests.get(
            PPAC_URL,
            timeout=30,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Fare Keralam official data updater)"
                ),
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml,"
                    "application/xml;q=0.9,"
                    "*/*;q=0.8"
                ),
                "Accept-Language": (
                    "en-IN,en;q=0.9"
                )
            }
        )

        response.raise_for_status()

        html = response.text

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # ----------------------------------------------------
        # LINKS
        # ----------------------------------------------------

        links = []

        for link in soup.find_all(
            "a",
            href=True
        ):

            text = link.get_text(
                " ",
                strip=True
            )

            href = link.get("href")

            if text or href:

                links.append({
                    "text": text[:200],
                    "href": href
                })

        # ----------------------------------------------------
        # SCRIPTS
        # ----------------------------------------------------

        scripts = []

        for script in soup.find_all(
            "script",
            src=True
        ):

            scripts.append(
                script.get("src")
            )

        # ----------------------------------------------------
        # TABLES
        # ----------------------------------------------------

        tables = []

        for index, table in enumerate(
            soup.find_all("table")[:20]
        ):

            rows = []

            for row in table.find_all("tr")[:20]:

                cells = [
                    cell.get_text(
                        " ",
                        strip=True
                    )
                    for cell in row.find_all(
                        ["th", "td"]
                    )
                ]

                if cells:
                    rows.append(cells)

            tables.append({
                "table_index": index,
                "rows": rows
            })

        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return {

            "success": True,

            "status_code":
                response.status_code,

            "final_url":
                response.url,

            "page_title": (
                soup.title.get_text(
                    strip=True
                )
                if soup.title
                else None
            ),

            "html_size":
                len(html),

            "link_count":
                len(links),

            "script_count":
                len(scripts),

            "table_count":
                len(tables),

            "links":
                links[:100],

            "scripts":
                scripts[:100],

            "tables":
                tables
        }

    except requests.RequestException as error:

        raise HTTPException(
            status_code=502,
            detail=(
                f"PPAC request failed: "
                f"{str(error)}"
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# END
# ============================================================