import os
from datetime import date, datetime
from typing import Any

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import Client, create_client


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
UPDATE_TOKEN = os.getenv("FUEL_UPDATE_TOKEN")


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Fare Keralam API",
    description="Kerala fare and operating-cost calculation API",
    version="1.2.0",
)


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
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )
    except Exception:
        supabase = None


def require_database():
    if supabase is None:
        raise HTTPException(
            status_code=500,
            detail="Database is not configured",
        )


# ============================================================
# OFFICIAL DATA SOURCES
# ============================================================

PPAC_URL = (
    "https://ppac.gov.in/"
    "retail-selling-price-rsp-of-petrol-diesel-and-domestic-lpg/"
    "price-build-up-of-petrol-and-diesel"
)

IOCL_PRICE_URL = (
    "https://www.iocl.com/petrol-diesel-price"
)

BPCL_URL = (
    "https://www.bharatpetroleum.in/index.aspx"
)

HPCL_PRICE_URL = (
    "https://www.hindustanpetroleum.com/PriceBuildup"
)


SOURCE_URLS = {
    "PPAC": PPAC_URL,
    "IOCL": IOCL_PRICE_URL,
    "BPCL": BPCL_URL,
    "HPCL": HPCL_PRICE_URL,
}


COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def root():
    return {
        "name": "Fare Keralam API",
        "status": "online",
        "version": "1.2.0",
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "database_configured": supabase is not None,
        "fuel_update_token_configured": UPDATE_TOKEN is not None,
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
            "vehicles": response.data,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# CATEGORIES
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
            "categories": response.data,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
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
            "energy_sources": response.data,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# PRICE HISTORY
# ============================================================

@app.get("/api/prices")
def get_prices(
    energy_source: str | None = Query(default=None),
    location: str = Query(default="Kerala"),
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
                    detail="Energy source not found",
                )

            energy_id = energy_response.data[0]["id"]

            query = query.eq(
                "energy_source_id",
                energy_id,
            )

        response = query.execute()

        return {
            "success": True,
            "count": len(response.data),
            "prices": response.data,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# LATEST PRICES
# ============================================================

@app.get("/api/latest-prices")
def get_latest_prices(
    location: str = Query(default="Kerala"),
):
    require_database()

    try:
        response = (
            supabase
            .table("price_history")
            .select("*")
            .eq("location", location)
            .order("price_date", desc=True)
            .limit(500)
            .execute()
        )

        latest = {}

        for item in response.data:
            key = (
                item.get("energy_source_id"),
                item.get("district"),
            )

            if key not in latest:
                latest[key] = item

        prices = list(latest.values())

        return {
            "success": True,
            "count": len(prices),
            "location": location,
            "prices": prices,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
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
            "sources": response.data,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


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
            "sources": response.data,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
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
            "fare_rules": response.data,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# FARE SLABS
# ============================================================

@app.get("/api/fare-slabs")
def get_fare_slabs(
    fare_rule_id: int | None = Query(default=None),
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
                fare_rule_id,
            )

        response = query.execute()

        return {
            "success": True,
            "count": len(response.data),
            "fare_slabs": response.data,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# COST DATA
# ============================================================

@app.get("/api/costs")
def get_costs(
    category: str | None = Query(default=None),
    location: str = Query(default="Kerala"),
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
                    detail="Cost category not found",
                )

            category_id = category_response.data[0]["id"]

            query = query.eq(
                "cost_category_id",
                category_id,
            )

        response = query.execute()

        return {
            "success": True,
            "count": len(response.data),
            "costs": response.data,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# DATABASE STATUS
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
            "fare_rules": fare_rules.count or 0,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# FUEL PRICE UPDATE MODEL
# ============================================================

class FuelPriceUpdate(BaseModel):
    fuel: str = Field(
        ...,
        description="Petrol or Diesel",
    )

    price: float = Field(
        ...,
        gt=0,
    )

    location: str = "Kerala"

    district: str | None = None

    price_date: date | None = None

    source_reference: str

    source_name: str = "PPAC Petrol and Diesel RSP"


# ============================================================
# FIND SOURCE
# ============================================================

def find_data_source(source_name: str):
    require_database()

    response = (
        supabase
        .table("data_sources")
        .select("id,name,url")
        .eq("name", source_name)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail=f"Data source not found: {source_name}",
        )

    return response.data[0]


# ============================================================
# MANUAL / VERIFIED FUEL PRICE UPDATE
# ============================================================

@app.post("/api/admin/update-fuel-price")
def update_fuel_price(
    data: FuelPriceUpdate,
    token: str = Query(...),
):
    """
    Insert a verified petrol/diesel price into price_history.

    This endpoint does not scrape prices.
    It stores a price only after a verified value is supplied.
    """

    require_database()

    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------

    if not UPDATE_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="FUEL_UPDATE_TOKEN is not configured",
        )

    if token != UPDATE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid update token",
        )

    # --------------------------------------------------------
    # VALIDATE FUEL
    # --------------------------------------------------------

    fuel_name = data.fuel.strip().title()

    if fuel_name not in ["Petrol", "Diesel"]:
        raise HTTPException(
            status_code=400,
            detail="Only Petrol and Diesel are supported currently",
        )

    # --------------------------------------------------------
    # ENERGY SOURCE
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
            detail=f"{fuel_name} energy source not found",
        )

    energy_source = energy_response.data[0]

    # --------------------------------------------------------
    # COST CATEGORY
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
            detail=f"{fuel_name} cost category not found",
        )

    cost_category = category_response.data[0]

    # --------------------------------------------------------
    # DATA SOURCE
    # --------------------------------------------------------

    source = find_data_source(
        data.source_name
    )

    source_id = source["id"]

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
            cost_category["id"],
        )
        .eq(
            "energy_source_id",
            energy_source["id"],
        )
        .eq(
            "location",
            data.location,
        )
        .eq(
            "price_date",
            str(effective_date),
        )
    )

    if data.district is None:
        existing_query = existing_query.is_(
            "district",
            "null",
        )
    else:
        existing_query = existing_query.eq(
            "district",
            data.district,
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
                "A price record already exists for "
                "this fuel, location, district and date"
            ),
            "record": existing.data[0],
        }

    # --------------------------------------------------------
    # INSERT
    # --------------------------------------------------------

    record = {
        "cost_category_id": cost_category["id"],
        "energy_source_id": energy_source["id"],
        "value": data.price,
        "unit": energy_source["unit"],
        "location": data.location,
        "district": data.district,
        "price_date": str(effective_date),
        "source_id": source_id,
        "source_reference": data.source_reference,
        "retrieved_at": datetime.utcnow().isoformat(),
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
                f"{fuel_name} price stored successfully"
            ),
            "record": (
                response.data[0]
                if response.data
                else record
            ),
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# GENERIC OFFICIAL SOURCE FETCHER
# ============================================================

def fetch_official_page(
    source_name: str,
    url: str,
) -> dict[str, Any]:
    """
    Read-only fetch.

    This function NEVER writes to Supabase.
    """

    try:
        response = requests.get(
            url,
            timeout=30,
            allow_redirects=True,
            headers=COMMON_HEADERS,
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        page_text = soup.get_text(
            " ",
            strip=True,
        )

        title = (
            soup.title.get_text(strip=True)
            if soup.title
            else None
        )

        return {
            "success": True,
            "source": source_name,
            "source_url": url,
            "status_code": response.status_code,
            "final_url": response.url,
            "page_size": len(response.text),
            "page_title": title,
            "redirect_history": [
                {
                    "status_code": item.status_code,
                    "url": item.url,
                    "location": item.headers.get(
                        "Location"
                    ),
                }
                for item in response.history
            ],
            "response_location": response.headers.get(
                "Location"
            ),
            "contains_petrol": (
                "petrol" in page_text.lower()
            ),
            "contains_diesel": (
                "diesel" in page_text.lower()
            ),
            "contains_kerala": (
                "kerala" in page_text.lower()
            ),
            "html_size": len(response.text),
        }

    except requests.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail=(
                f"{source_name} request failed: "
                f"{str(error)}"
            ),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# PPAC TEST
# ============================================================

@app.get("/api/admin/test-ppac")
def test_ppac(
    token: str = Query(...),
):
    """
    Read-only PPAC connectivity test.
    """

    if not UPDATE_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="FUEL_UPDATE_TOKEN is not configured",
        )

    if token != UPDATE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid update token",
        )

    result = fetch_official_page(
        "PPAC",
        PPAC_URL,
    )

    soup = BeautifulSoup(
        requests.get(
            PPAC_URL,
            timeout=30,
            headers=COMMON_HEADERS,
        ).text,
        "html.parser",
    )

    result["table_count"] = len(
        soup.find_all("table")
    )

    return result


# ============================================================
# PPAC STRUCTURE INSPECTION
# ============================================================

@app.get("/api/admin/inspect-ppac")
def inspect_ppac(
    token: str = Query(...),
):
    """
    Read-only PPAC structure diagnostic.

    This endpoint is useful because PPAC currently exposes
    official IOC/BPCL/HPCL links rather than a normal HTML
    table containing the state RSP values.
    """

    if not UPDATE_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="FUEL_UPDATE_TOKEN is not configured",
        )

    if token != UPDATE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid update token",
        )

    try:
        response = requests.get(
            PPAC_URL,
            timeout=30,
            allow_redirects=True,
            headers=COMMON_HEADERS,
        )

        response.raise_for_status()

        html = response.text

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        links = []

        for link in soup.find_all(
            "a",
            href=True,
        ):
            text = link.get_text(
                " ",
                strip=True,
            )

            href = link.get("href")

            if text or href:
                links.append(
                    {
                        "text": text[:200],
                        "href": href,
                    }
                )

        scripts = []

        for script in soup.find_all(
            "script",
            src=True,
        ):
            scripts.append(
                script.get("src")
            )

        tables = soup.find_all("table")

        return {
            "success": True,
            "status_code": response.status_code,
            "final_url": response.url,
            "page_title": (
                soup.title.get_text(
                    strip=True
                )
                if soup.title
                else None
            ),
            "html_size": len(html),
            "link_count": len(links),
            "script_count": len(scripts),
            "table_count": len(tables),
            "contains_petrol": (
                "petrol"
                in soup.get_text(
                    " ",
                    strip=True,
                ).lower()
            ),
            "contains_diesel": (
                "diesel"
                in soup.get_text(
                    " ",
                    strip=True,
                ).lower()
            ),
            "contains_kerala": (
                "kerala"
                in soup.get_text(
                    " ",
                    strip=True,
                ).lower()
            ),
            "links": links[:150],
            "scripts": scripts[:100],
        }

    except requests.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail=f"PPAC request failed: {str(error)}",
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# INDIANOIL / IOC TEST
# ============================================================

@app.get("/api/admin/test-iocl")
def test_iocl(
    token: str = Query(...),
):
    """
    Read-only IndianOil connection test.
    """

    if not UPDATE_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="FUEL_UPDATE_TOKEN is not configured",
        )

    if token != UPDATE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid update token",
        )

    return fetch_official_page(
        "IOCL",
        IOCL_PRICE_URL,
    )


# ============================================================
# BPCL TEST
# ============================================================

@app.get("/api/admin/test-bpcl")
def test_bpcl(
    token: str = Query(...),
):
    """
    Read-only BPCL connection test.
    """

    if not UPDATE_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="FUEL_UPDATE_TOKEN is not configured",
        )

    if token != UPDATE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid update token",
        )

    return fetch_official_page(
        "BPCL",
        BPCL_URL,
    )


# ============================================================
# HPCL TEST
# ============================================================

@app.get("/api/admin/test-hpcl")
def test_hpcl(
    token: str = Query(...),
):
    """
    Read-only HPCL connection test.
    """

    if not UPDATE_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="FUEL_UPDATE_TOKEN is not configured",
        )

    if token != UPDATE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid update token",
        )

    return fetch_official_page(
        "HPCL",
        HPCL_PRICE_URL,
    )


# ============================================================
# ALL OFFICIAL SOURCES TEST
# ============================================================

@app.get("/api/admin/test-all-fuel-sources")
def test_all_fuel_sources(
    token: str = Query(...),
):
    """
    Test PPAC + IOC + BPCL + HPCL.

    Read-only.
    No database writes.
    """

    if not UPDATE_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="FUEL_UPDATE_TOKEN is not configured",
        )

    if token != UPDATE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid update token",
        )

    results = {}

    for name, url in SOURCE_URLS.items():

        try:
            results[name] = fetch_official_page(
                name,
                url,
            )

        except HTTPException as error:
            results[name] = {
                "success": False,
                "error": error.detail,
            }

        except Exception as error:
            results[name] = {
                "success": False,
                "error": str(error),
            }

    return {
        "success": True,
        "message": (
            "Official fuel-source connectivity "
            "diagnostic completed"
        ),
        "sources": results,
    }


# ============================================================
# OFFICIAL SOURCE LINKS
# ============================================================

@app.get("/api/admin/fuel-source-links")
def fuel_source_links(
    token: str = Query(...),
):
    """
    Returns the official sources currently used by
    Fare Keralam.
    """

    if not UPDATE_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="FUEL_UPDATE_TOKEN is not configured",
        )

    if token != UPDATE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid update token",
        )

    return {
        "success": True,
        "sources": [
            {
                "name": "PPAC",
                "organization": (
                    "Petroleum Planning & Analysis Cell"
                ),
                "url": PPAC_URL,
                "role": (
                    "Government petroleum data/reference source"
                ),
            },
            {
                "name": "IOCL",
                "organization": "Indian Oil Corporation Limited",
                "url": IOCL_PRICE_URL,
                "role": "Official oil marketing company source",
            },
            {
                "name": "BPCL",
                "organization": "Bharat Petroleum Corporation Limited",
                "url": BPCL_URL,
                "role": "Official oil marketing company source",
            },
            {
                "name": "HPCL",
                "organization": (
                    "Hindustan Petroleum Corporation Limited"
                ),
                "url": HPCL_PRICE_URL,
                "role": "Official oil marketing company source",
            },
        ],
    }


# ============================================================
# FUEL SOURCE STATUS
# ============================================================

@app.get("/api/admin/fuel-source-status")
def fuel_source_status(
    token: str = Query(...),
):
    """
    Lightweight health check for all official fuel sources.
    """

    if not UPDATE_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="FUEL_UPDATE_TOKEN is not configured",
        )

    if token != UPDATE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid update token",
        )

    output = []

    for name, url in SOURCE_URLS.items():

        try:
            result = fetch_official_page(
                name,
                url,
            )

            output.append(
                {
                    "source": name,
                    "online": result["success"],
                    "status_code": result["status_code"],
                    "final_url": result["final_url"],
                    "contains_petrol": (
                        result["contains_petrol"]
                    ),
                    "contains_diesel": (
                        result["contains_diesel"]
                    ),
                    "contains_kerala": (
                        result["contains_kerala"]
                    ),
                }
            )

        except Exception as error:
            output.append(
                {
                    "source": name,
                    "online": False,
                    "error": str(error),
                }
            )

    return {
        "success": True,
        "sources": output,
    }


# ============================================================
# PPAC → OMC LINK DISCOVERY
# ============================================================

@app.get("/api/admin/discover-fuel-links")
def discover_fuel_links(
    token: str = Query(...),
):
    """
    Reads PPAC and discovers the official links it exposes
    for IOC, BPCL and HPCL.

    Read-only.
    """

    if not UPDATE_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="FUEL_UPDATE_TOKEN is not configured",
        )

    if token != UPDATE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid update token",
        )

    try:
        response = requests.get(
            PPAC_URL,
            timeout=30,
            allow_redirects=True,
            headers=COMMON_HEADERS,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        discovered = []

        for link in soup.find_all(
            "a",
            href=True,
        ):
            text = link.get_text(
                " ",
                strip=True,
            )

            href = link.get("href")

            if not text:
                continue

            lower_text = text.lower()

            if (
                "as per ioc" in lower_text
                or "as per bpc" in lower_text
                or "as per hpc" in lower_text
                or "indianoil" in lower_text
                or "bharat petroleum" in lower_text
                or "hindustan petroleum" in lower_text
            ):
                discovered.append(
                    {
                        "text": text,
                        "href": href,
                    }
                )

        return {
            "success": True,
            "ppac_url": PPAC_URL,
            "count": len(discovered),
            "links": discovered,
        }

    except requests.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail=f"PPAC request failed: {str(error)}",
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# DEPLOYMENT DIAGNOSTIC
# ============================================================

@app.get("/api/deployment")
def deployment_info():
    """
    Helps diagnose Render deployment configuration.
    """

    return {
        "success": True,
        "service": "Fare Keralam API",
        "python_module": "main:app",
        "recommended_start_command": (
            "uvicorn main:app --host 0.0.0.0 --port $PORT"
        ),
        "database_configured": (
            supabase is not None
        ),
        "fuel_update_token_configured": (
            UPDATE_TOKEN is not None
        ),
    }