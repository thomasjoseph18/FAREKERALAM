# ============================================================
# FARE KERALAM - MAIN API
# ============================================================
# FastAPI backend for:
#   - Vehicle categories
#   - Energy sources
#   - Vehicles
#   - Vehicle options
#   - Fare calculation
#   - Health check
#
# Designed for:
#   Supabase PostgreSQL
#   Render
# ============================================================

import os
import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Any

import psycopg2
import psycopg2.extras

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("WARNING: DATABASE_URL is not configured.")


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Fare Keralam API",
    description="Kerala passenger transport fare calculation API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Creates a PostgreSQL connection using DATABASE_URL.
    Works with Supabase PostgreSQL.
    """

    if not DATABASE_URL:
        raise HTTPException(
            status_code=500,
            detail="Database is not configured"
        )

    try:
        return psycopg2.connect(
            DATABASE_URL,
            cursor_factory=psycopg2.extras.RealDictCursor
        )

    except Exception as exc:
        print("Database connection error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Unable to connect to database"
        )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_name(value: Optional[str]) -> str:
    """
    Normalizes names so that:
        Taxi / Motor Cab
        taxi/motor cab
        Motor Cab
        MOTOR CAB

    can be compared safely.
    """

    if not value:
        return ""

    value = value.strip().lower()

    replacements = {
        "/": " ",
        "-": " ",
        "_": " ",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = " ".join(value.split())

    return value


# ------------------------------------------------------------
# Category aliases
# ------------------------------------------------------------

CATEGORY_ALIASES = {
    "auto": "Auto Rickshaw",
    "auto rickshaw": "Auto Rickshaw",

    "taxi": "Motor Cab",
    "motor cab": "Motor Cab",
    "taxi motor cab": "Motor Cab",
    "taxi / motor cab": "Motor Cab",

    "maxicab": "Maxicab",
    "maxi cab": "Maxicab",

    "contract carriage": "Contract Carriage",

    "stage carriage": "Stage Carriage",

    "traveller": "Contract Carriage",
    "traveler": "Contract Carriage",

    "route bus": "Stage Carriage",

    "tourist bus": "Contract Carriage",
}


def canonical_category_name(category: Optional[str]) -> Optional[str]:
    """
    Converts frontend/category aliases into the actual
    category names stored in the database.
    """

    if not category:
        return None

    normalized = normalize_name(category)

    return CATEGORY_ALIASES.get(
        normalized,
        category.strip()
    )


# ============================================================
# GENERIC DATABASE HELPERS
# ============================================================

def fetch_one(query: str, params=()):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    finally:
        conn.close()


def fetch_all(query: str, params=()):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    finally:
        conn.close()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "success": True,
        "name": "Fare Keralam API",
        "version": "1.0.0",
        "status": "online",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():

    database_configured = bool(DATABASE_URL)

    database_connected = False

    if database_configured:
        try:
            conn = get_connection()

            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            conn.close()

            database_connected = True

        except Exception as exc:
            print("Health DB error:", exc)

    return {
        "status": "healthy" if database_connected else "degraded",
        "database_configured": database_configured,
        "database_connected": database_connected,
    }


# ============================================================
# CATEGORIES
# ============================================================

@app.get("/api/categories")
def get_categories():

    query = """
        SELECT
            id,
            name,
            description,
            requires_model,
            requires_seating_capacity,
            active,
            created_at
        FROM vehicle_categories
        WHERE active = TRUE
        ORDER BY id
    """

    try:
        categories = fetch_all(query)

        return {
            "success": True,
            "count": len(categories),
            "categories": categories,
        }

    except Exception as exc:

        print("Categories error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Unable to load vehicle categories"
        )


# ============================================================
# ENERGY SOURCES
# ============================================================

@app.get("/api/energy-sources")
def get_energy_sources():

    query = """
        SELECT
            id,
            name,
            unit,
            description,
            active,
            created_at
        FROM energy_sources
        WHERE active = TRUE
        ORDER BY id
    """

    try:

        energy_sources = fetch_all(query)

        return {
            "success": True,
            "count": len(energy_sources),
            "energy_sources": energy_sources,
        }

    except Exception as exc:

        print("Energy source error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Unable to load energy sources"
        )


# ============================================================
# VEHICLES
# ============================================================

@app.get("/api/vehicles")
def get_vehicles(
    category: Optional[str] = None,
    energy: Optional[str] = None,
    seating_capacity: Optional[int] = None,
):

    query = """
        SELECT
            v.id,
            v.category_id,
            v.energy_source_id,
            v.name,
            v.seating_capacity,
            v.efficiency,
            v.efficiency_unit,
            v.active,
            v.created_at
        FROM vehicles v
        WHERE v.active = TRUE
    """

    params = []

    # --------------------------------------------------------
    # Category filter
    # --------------------------------------------------------

    if category:

        category = canonical_category_name(category)

        query += """
            AND v.category_id = (
                SELECT id
                FROM vehicle_categories
                WHERE LOWER(name) = LOWER(%s)
                LIMIT 1
            )
        """

        params.append(category)

    # --------------------------------------------------------
    # Energy filter
    # --------------------------------------------------------

    if energy:

        query += """
            AND v.energy_source_id = (
                SELECT id
                FROM energy_sources
                WHERE LOWER(name) = LOWER(%s)
                LIMIT 1
            )
        """

        params.append(energy.strip())

    # --------------------------------------------------------
    # Seating filter
    # --------------------------------------------------------

    if seating_capacity is not None:

        query += """
            AND v.seating_capacity = %s
        """

        params.append(seating_capacity)

    query += """
        ORDER BY v.id
    """

    try:

        vehicles = fetch_all(query, params)

        return {
            "success": True,
            "count": len(vehicles),
            "vehicles": vehicles,
        }

    except Exception as exc:

        print("Vehicles error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Unable to load vehicles"
        )


# ============================================================
# VEHICLE OPTIONS
# ============================================================

@app.get("/api/vehicle-options")
def get_vehicle_options():

    query = """
        SELECT
            vc.name AS category,
            es.name AS energy,
            v.seating_capacity
        FROM vehicles v
        INNER JOIN vehicle_categories vc
            ON vc.id = v.category_id
        INNER JOIN energy_sources es
            ON es.id = v.energy_source_id
        WHERE v.active = TRUE
        ORDER BY
            vc.id,
            es.id,
            v.seating_capacity
    """

    try:

        rows = fetch_all(query)

        result = {}

        for row in rows:

            category = row["category"]
            energy = row["energy"]
            seating = row["seating_capacity"]

            if category not in result:
                result[category] = {}

            if energy not in result[category]:
                result[category][energy] = []

            if seating is not None:
                if seating not in result[category][energy]:
                    result[category][energy].append(seating)

        # ----------------------------------------------------
        # Make sure every known energy source exists
        # ----------------------------------------------------

        energy_names = [
            "Petrol",
            "Diesel",
            "CNG",
            "Electricity",
            "Hybrid",
        ]

        categories = [
            "Auto Rickshaw",
            "Motor Cab",
            "Maxicab",
            "Contract Carriage",
            "Stage Carriage",
        ]

        for category in categories:

            if category not in result:
                result[category] = {}

            for energy in energy_names:

                if energy not in result[category]:
                    result[category][energy] = []

        return {
            "success": True,
            "categories": result,
        }

    except Exception as exc:

        print("Vehicle options error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Unable to load vehicle options"
        )


# ============================================================
# FARE CALCULATION REQUEST
# ============================================================

class FareCalculationRequest(BaseModel):

    category: str = Field(
        ...,
        description="Vehicle category"
    )

    energy_source: Optional[str] = Field(
        None,
        description="Petrol, Diesel, CNG, Electricity or Hybrid"
    )

    distance_km: float = Field(
        ...,
        gt=0,
        description="Journey distance in kilometres"
    )

    seating_capacity: Optional[int] = Field(
        None,
        gt=0
    )

    vehicle_id: Optional[int] = None


# ============================================================
# ROUNDING
# ============================================================

def money(value: float) -> float:

    amount = Decimal(str(value))

    rounded = amount.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    return float(rounded)


# ============================================================
# FIND CATEGORY
# ============================================================

def find_category(category_name: str):

    canonical = canonical_category_name(category_name)

    query = """
        SELECT
            id,
            name,
            description,
            requires_model,
            requires_seating_capacity,
            active
        FROM vehicle_categories
        WHERE active = TRUE
          AND LOWER(name) = LOWER(%s)
        LIMIT 1
    """

    return fetch_one(
        query,
        (canonical,)
    )


# ============================================================
# FIND ENERGY SOURCE
# ============================================================

def find_energy_source(energy_name: Optional[str]):

    if not energy_name:
        return None

    query = """
        SELECT
            id,
            name,
            unit
        FROM energy_sources
        WHERE active = TRUE
          AND LOWER(name) = LOWER(%s)
        LIMIT 1
    """

    return fetch_one(
        query,
        (energy_name.strip(),)
    )


# ============================================================
# FIND VEHICLE
# ============================================================

def find_vehicle(
    category_id: int,
    energy_source_id: Optional[int],
    seating_capacity: Optional[int],
    vehicle_id: Optional[int],
):

    # --------------------------------------------------------
    # Direct vehicle ID
    # --------------------------------------------------------

    if vehicle_id is not None:

        query = """
            SELECT
                id,
                category_id,
                energy_source_id,
                name,
                seating_capacity,
                efficiency,
                efficiency_unit
            FROM vehicles
            WHERE id = %s
              AND active = TRUE
            LIMIT 1
        """

        return fetch_one(
            query,
            (vehicle_id,)
        )

    # --------------------------------------------------------
    # Match category + energy + seating
    # --------------------------------------------------------

    if seating_capacity is not None:

        query = """
            SELECT
                id,
                category_id,
                energy_source_id,
                name,
                seating_capacity,
                efficiency,
                efficiency_unit
            FROM vehicles
            WHERE category_id = %s
              AND active = TRUE
              AND seating_capacity = %s
        """

        params = [
            category_id,
            seating_capacity,
        ]

        if energy_source_id is not None:

            query += """
                AND energy_source_id = %s
            """

            params.append(energy_source_id)

        query += """
            ORDER BY id
            LIMIT 1
        """

        return fetch_one(
            query,
            params
        )

    # --------------------------------------------------------
    # Match category + energy
    # --------------------------------------------------------

    query = """
        SELECT
            id,
            category_id,
            energy_source_id,
            name,
            seating_capacity,
            efficiency,
            efficiency_unit
        FROM vehicles
        WHERE category_id = %s
          AND active = TRUE
    """

    params = [category_id]

    if energy_source_id is not None:

        query += """
            AND energy_source_id = %s
        """

        params.append(energy_source_id)

    query += """
        ORDER BY id
        LIMIT 1
    """

    return fetch_one(
        query,
        params
    )


# ============================================================
# FARE RULE LOOKUP
# ============================================================

def find_fare_rule(
    category_id: int,
    energy_source_id: Optional[int],
    seating_capacity: Optional[int],
):
    """
    Attempts to locate a fare rule.

    The function first tries a category + energy specific rule.

    If no energy-specific rule exists, it falls back to a
    category-only rule.

    This allows government-approved/base fare rules to remain
    independent from fuel-cost adjustments.
    """

    # --------------------------------------------------------
    # First: category + energy
    # --------------------------------------------------------

    if energy_source_id is not None:

        query = """
            SELECT *
            FROM fare_rules
            WHERE vehicle_category_id = %s
              AND energy_source_id = %s
            ORDER BY id DESC
            LIMIT 1
        """

        try:

            rule = fetch_one(
                query,
                (
                    category_id,
                    energy_source_id,
                )
            )

            if rule:
                return rule

        except Exception as exc:

            print(
                "Energy-specific fare rule lookup failed:",
                exc
            )

    # --------------------------------------------------------
    # Second: category only
    # --------------------------------------------------------

    query = """
        SELECT *
        FROM fare_rules
        WHERE vehicle_category_id = %s
        ORDER BY id DESC
        LIMIT 1
    """

    try:

        return fetch_one(
            query,
            (category_id,)
        )

    except Exception as exc:

        print(
            "Category fare rule lookup failed:",
            exc
        )

        return None


# ============================================================
# FARE SLAB LOOKUP
# ============================================================

def find_fare_slabs(fare_rule_id: int):

    """
    Reads slabs belonging to a fare rule.

    Expected logical structure:

        fare_slabs
        ----------
        id
        fare_rule_id
        from_km
        to_km
        rate_per_km
        fixed_fare

    The function gracefully returns an empty list if the
    table/columns are not yet available.
    """

    query = """
        SELECT *
        FROM fare_slabs
        WHERE fare_rule_id = %s
        ORDER BY
            COALESCE(from_km, 0),
            id
    """

    try:

        return fetch_all(
            query,
            (fare_rule_id,)
        )

    except Exception as exc:

        print(
            "Fare slab lookup failed:",
            exc
        )

        return []


# ============================================================
# SLAB CALCULATION
# ============================================================

def calculate_from_slabs(
    distance_km: float,
    slabs,
):
    """
    Calculates fare progressively through distance slabs.

    Supported possible column names:

        from_km
        to_km
        rate_per_km
        per_km_rate
        rate
        fixed_fare
        amount
    """

    if not slabs:
        return None

    total = 0.0

    remaining = distance_km

    for slab in slabs:

        from_km = slab.get("from_km")

        to_km = slab.get("to_km")

        rate = (
            slab.get("rate_per_km")
            if slab.get("rate_per_km") is not None
            else slab.get("per_km_rate")
        )

        if rate is None:
            rate = slab.get("rate")

        fixed_fare = slab.get("fixed_fare")

        if fixed_fare is None:
            fixed_fare = slab.get("amount")

        # ----------------------------------------------------
        # Fixed fare slab
        # ----------------------------------------------------

        if fixed_fare is not None:

            if (
                to_km is None
                or distance_km <= float(to_km)
            ):

                return money(float(fixed_fare))

        # ----------------------------------------------------
        # Rate-based slab
        # ----------------------------------------------------

        if rate is None:
            continue

        rate = float(rate)

        start = (
            float(from_km)
            if from_km is not None
            else 0.0
        )

        if to_km is None:

            end = distance_km

        else:

            end = min(
                distance_km,
                float(to_km)
            )

        if end > start:

            kilometres = end - start

            total += kilometres * rate

        if distance_km <= end:
            break

    return money(total)


# ============================================================
# DEFAULT FARE CALCULATION
# ============================================================

def calculate_default_fare(
    category_name: str,
    distance_km: float,
):
    """
    Safe fallback.

    IMPORTANT:
    These values are not claimed to be current Kerala
    government fares. They are only used when no fare rule
    exists in the database.

    Replace them with the actual approved fare data before
    production use.
    """

    category = canonical_category_name(category_name)

    defaults = {

        "Auto Rickshaw": {
            "base_fare": 30.0,
            "base_distance": 1.5,
            "per_km": 15.0,
        },

        "Motor Cab": {
            "base_fare": 100.0,
            "base_distance": 2.0,
            "per_km": 18.0,
        },

        "Maxicab": {
            "base_fare": 150.0,
            "base_distance": 2.0,
            "per_km": 25.0,
        },

        "Contract Carriage": {
            "base_fare": 200.0,
            "base_distance": 2.0,
            "per_km": 30.0,
        },

        "Stage Carriage": {
            "base_fare": 20.0,
            "base_distance": 1.0,
            "per_km": 5.0,
        },
    }

    rule = defaults.get(category)

    if not rule:
        return None

    if distance_km <= rule["base_distance"]:

        return money(
            rule["base_fare"]
        )

    extra_distance = (
        distance_km
        - rule["base_distance"]
    )

    fare = (
        rule["base_fare"]
        + extra_distance * rule["per_km"]
    )

    return money(fare)


# ============================================================
# MAIN FARE CALCULATOR
# ============================================================

@app.post("/api/fare/calculate")
def calculate_fare(
    request: FareCalculationRequest
):

    # --------------------------------------------------------
    # Validate distance
    # --------------------------------------------------------

    if request.distance_km <= 0:

        raise HTTPException(
            status_code=400,
            detail="Distance must be greater than zero"
        )

    # --------------------------------------------------------
    # Resolve category
    # --------------------------------------------------------

    category = find_category(
        request.category
    )

    if not category:

        # IMPORTANT FIX:
        # Previously this returned:
        #
        #   Vehicle category not found
        #
        # when the frontend sent:
        #
        #   Taxi / Motor Cab
        #
        # while DB contained:
        #
        #   Motor Cab
        #
        canonical = canonical_category_name(
            request.category
        )

        raise HTTPException(
            status_code=404,
            detail={
                "message": "Vehicle category not found",
                "requested": request.category,
                "normalized": canonical,
            }
        )

    category_id = category["id"]

    category_name = category["name"]

    # --------------------------------------------------------
    # Resolve energy
    # --------------------------------------------------------

    energy = find_energy_source(
        request.energy_source
    )

    if request.energy_source and not energy:

        raise HTTPException(
            status_code=404,
            detail={
                "message": "Energy source not found",
                "requested": request.energy_source,
            }
        )

    energy_id = (
        energy["id"]
        if energy
        else None
    )

    # --------------------------------------------------------
    # Resolve vehicle
    # --------------------------------------------------------

    vehicle = find_vehicle(
        category_id=category_id,
        energy_source_id=energy_id,
        seating_capacity=request.seating_capacity,
        vehicle_id=request.vehicle_id,
    )

    # Vehicle is optional for simple category-based
    # calculations. Therefore we don't fail here.
    # --------------------------------------------------------

    # --------------------------------------------------------
    # Find fare rule
    # --------------------------------------------------------

    fare_rule = find_fare_rule(
        category_id=category_id,
        energy_source_id=energy_id,
        seating_capacity=request.seating_capacity,
    )

    fare = None

    calculation_method = None

    fare_rule_id = None

    # --------------------------------------------------------
    # Use database fare rule
    # --------------------------------------------------------

    if fare_rule:

        fare_rule_id = fare_rule.get("id")

        slabs = []

        if fare_rule_id:

            slabs = find_fare_slabs(
                fare_rule_id
            )

        if slabs:

            fare = calculate_from_slabs(
                request.distance_km,
                slabs
            )

            if fare is not None:
                calculation_method = "fare_slabs"

        # ----------------------------------------------------
        # Try common fare-rule fields
        # ----------------------------------------------------

        if fare is None:

            base_fare = (
                fare_rule.get("base_fare")
                if fare_rule.get("base_fare") is not None
                else fare_rule.get("minimum_fare")
            )

            if base_fare is None:
                base_fare = fare_rule.get("min_fare")

           base_distance = (
    fare_rule.get("minimum_distance_km")
    if fare_rule.get("minimum_distance_km") is not None
    else (
        fare_rule.get("base_distance_km")
        if fare_rule.get("base_distance_km") is not None
        else fare_rule.get("base_distance")
    )
)

            per_km = (
                fare_rule.get("per_km_rate")
                if fare_rule.get("per_km_rate") is not None
                else fare_rule.get("rate_per_km")
            )

            if per_km is None:
                per_km = fare_rule.get("per_km")

            if (
                base_fare is not None
                and base_distance is not None
                and per_km is not None
            ):

                base_fare = float(base_fare)

                base_distance = float(
                    base_distance
                )

                per_km = float(per_km)

                if request.distance_km <= base_distance:

                    fare = base_fare

                else:

                    extra_distance = (
                        request.distance_km
                        - base_distance
                    )

                    fare = (
                        base_fare
                        + extra_distance * per_km
                    )

                fare = money(fare)

                calculation_method = (
                    "fare_rule"
                )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    if fare is None:

        fare = calculate_default_fare(
            category_name,
            request.distance_km,
        )

        if fare is not None:

            calculation_method = (
                "fallback_default"
            )

    # --------------------------------------------------------
    # No fare available
    # --------------------------------------------------------

    if fare is None:

        raise HTTPException(
            status_code=422,
            detail={
                "message": (
                    "No fare rule is configured "
                    "for this vehicle category"
                ),
                "category": category_name,
                "energy_source": (
                    energy["name"]
                    if energy
                    else None
                ),
                "distance_km": request.distance_km,
            }
        )

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "success": True,

        "calculation": {
            "category": category_name,

            "energy_source": (
                energy["name"]
                if energy
                else None
            ),

            "distance_km": request.distance_km,

            "seating_capacity": (
                request.seating_capacity
            ),

            "vehicle": (
                {
                    "id": vehicle["id"],
                    "name": vehicle["name"],
                    "seating_capacity":
                        vehicle["seating_capacity"],
                }
                if vehicle
                else None
            ),

            "fare": fare,

            "currency": "INR",

            "calculation_method":
                calculation_method,

            "fare_rule_id":
                fare_rule_id,
        }
    }


# ============================================================
# SIMPLE GET FARE ENDPOINT
# ============================================================
# Useful for testing directly in browser.
#
# Example:
# /api/fare?category=Motor%20Cab&energy_source=Petrol&distance_km=20
# ============================================================

@app.get("/api/fare")
def get_fare(
    category: str,
    distance_km: float,
    energy_source: Optional[str] = None,
    seating_capacity: Optional[int] = None,
):

    request = FareCalculationRequest(
        category=category,
        energy_source=energy_source,
        distance_km=distance_km,
        seating_capacity=seating_capacity,
    )

    return calculate_fare(request)


# ============================================================
# DATABASE DIAGNOSTIC
# ============================================================

@app.get("/api/debug/category")
def debug_category(
    category: str
):

    canonical = canonical_category_name(
        category
    )

    row = find_category(
        category
    )

    return {
        "success": True,
        "requested": category,
        "normalized": normalize_name(category),
        "canonical": canonical,
        "database_match": row,
    }


# ============================================================
# DATABASE SUMMARY
# ============================================================

@app.get("/api/debug/database")
def database_summary():

    result = {}

    tables = [
        "vehicle_categories",
        "energy_sources",
        "vehicles",
        "fare_rules",
        "fare_slabs",
        "cost_data",
        "price_history",
    ]

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            for table in tables:

                try:

                    cursor.execute(
                        f"""
                        SELECT COUNT(*) AS count
                        FROM {table}
                        """
                    )

                    row = cursor.fetchone()

                    result[table] = row["count"]

                except Exception as exc:

                    conn.rollback()

                    result[table] = {
                        "error": str(exc)
                    }

        return {
            "success": True,
            "tables": result,
        }

    finally:

        conn.close()


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():

    print("=" * 60)
    print("FARE KERALAM API STARTING")
    print("=" * 60)

    if DATABASE_URL:

        print("Database: CONFIGURED")

        try:

            conn = psycopg2.connect(
                DATABASE_URL
            )

            conn.close()

            print("Database connection: OK")

        except Exception as exc:

            print(
                "Database connection failed:",
                exc
            )

    else:

        print(
            "Database: NOT CONFIGURED"
        )

    print("=" * 60)


# ============================================================
# RENDER ENTRY POINT
# ============================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.getenv(
            "PORT",
            "8000"
        )
    )

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )