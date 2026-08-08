# ============================================================
# FARE KERALAM - MAIN API
# ============================================================
# FastAPI backend
# Designed for:
#   - Supabase PostgreSQL
#   - Render
#   - Vehicle categories
#   - Energy sources
#   - Vehicles
#   - Vehicle options
#   - Fare calculation
#   - Database diagnostics
# ============================================================

import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

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
    version="1.1.0",
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
    Connect to Supabase PostgreSQL using DATABASE_URL.
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
# DATABASE HELPERS
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
# NAME NORMALIZATION
# ============================================================

def normalize_name(value: Optional[str]) -> str:

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

    return " ".join(value.split())


# ============================================================
# CATEGORY ALIASES
# ============================================================

CATEGORY_ALIASES = {

    "auto":
        "Auto Rickshaw",

    "auto rickshaw":
        "Auto Rickshaw",

    "taxi":
        "Motor Cab",

    "motor cab":
        "Motor Cab",

    "taxi motor cab":
        "Motor Cab",

    "taxi / motor cab":
        "Motor Cab",

    "maxicab":
        "Maxicab",

    "maxi cab":
        "Maxicab",

    "contract carriage":
        "Contract Carriage",

    "stage carriage":
        "Stage Carriage",

    "traveller":
        "Contract Carriage",

    "traveler":
        "Contract Carriage",

    "route bus":
        "Stage Carriage",

    "tourist bus":
        "Contract Carriage",
}


def canonical_category_name(
    category: Optional[str]
) -> Optional[str]:

    if not category:
        return None

    normalized = normalize_name(category)

    return CATEGORY_ALIASES.get(
        normalized,
        category.strip()
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "success": True,
        "name": "Fare Keralam API",
        "version": "1.1.0",
        "status": "online",
    }


# ============================================================
# HEALTH CHECK
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

            print("Health database error:", exc)

    return {

        "status":
            "healthy"
            if database_connected
            else "degraded",

        "database_configured":
            database_configured,

        "database_connected":
            database_connected,
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

    # Category filter
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

    # Energy filter
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

    # Seating filter
    if seating_capacity is not None:

        query += """
            AND v.seating_capacity = %s
        """

        params.append(seating_capacity)

    query += """
        ORDER BY v.id
    """

    try:

        vehicles = fetch_all(
            query,
            params
        )

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

                    result[category][energy].append(
                        seating
                    )

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
        gt=0,
        description="Passenger seating capacity"
    )

    vehicle_id: Optional[int] = Field(
        None,
        gt=0,
        description="Optional vehicle ID"
    )


# ============================================================
# MONEY ROUNDING
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

    canonical = canonical_category_name(
        category_name
    )

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

def find_energy_source(
    energy_name: Optional[str]
):

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
    # Category + energy + seating
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

            params.append(
                energy_source_id
            )

        query += """
            ORDER BY id
            LIMIT 1
        """

        return fetch_one(
            query,
            params
        )

    # --------------------------------------------------------
    # Category + energy
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

    params = [
        category_id
    ]

    if energy_source_id is not None:

        query += """
            AND energy_source_id = %s
        """

        params.append(
            energy_source_id
        )

    query += """
        ORDER BY id
        LIMIT 1
    """

    return fetch_one(
        query,
        params
    )


# ============================================================
# FIND FARE RULE
# ============================================================

def find_fare_rule(
    category_id: int,
    energy_source_id: Optional[int],
):

    # --------------------------------------------------------
    # Try category + energy first
    # --------------------------------------------------------

    if energy_source_id is not None:

        query = """
            SELECT *
            FROM fare_rules
            WHERE vehicle_category_id = %s
              AND energy_source_id = %s
              AND status = 'active'
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
    # Category-only rule
    # --------------------------------------------------------

    query = """
        SELECT *
        FROM fare_rules
        WHERE vehicle_category_id = %s
          AND energy_source_id IS NULL
          AND status = 'active'
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
# FIND FARE SLABS
# ============================================================

def find_fare_slabs(
    fare_rule_id: int
):

    query = """
        SELECT
            id,
            fare_rule_id,
            from_km,
            to_km,
            rate_per_km,
            created_at
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
# CALCULATE USING FARE SLABS
# ============================================================

def calculate_from_slabs(
    distance_km: float,
    minimum_fare: float,
    minimum_distance_km: float,
    slabs,
):
    """
    Calculates:

        minimum fare
        +
        additional distance × slab rate

    Example:

        Minimum fare = ₹30
        Minimum distance = 1.5 km
        Rate = ₹15/km

        5 km:

        ₹30 + (5 - 1.5) × ₹15
        = ₹82.50
    """

    # --------------------------------------------------------
    # Journey within minimum distance
    # --------------------------------------------------------

    if distance_km <= minimum_distance_km:

        return money(
            minimum_fare
        )

    total = float(
        minimum_fare
    )

    previous_distance = float(
        minimum_distance_km
    )

    # --------------------------------------------------------
    # Apply slabs
    # --------------------------------------------------------

    for slab in slabs:

        from_km = slab.get(
            "from_km"
        )

        to_km = slab.get(
            "to_km"
        )

        rate = slab.get(
            "rate_per_km"
        )

        if rate is None:
            continue

        rate = float(rate)

        # If slab starts before the minimum distance,
        # start it from the minimum distance.

        if from_km is None:

            start = previous_distance

        else:

            start = max(
                float(from_km),
                previous_distance
            )

        # ----------------------------------------------------
        # Open-ended slab
        # ----------------------------------------------------

        if to_km is None:

            end = distance_km

        else:

            end = min(
                distance_km,
                float(to_km)
            )

        if end > start:

            kilometres = (
                end - start
            )

            total += (
                kilometres * rate
            )

        previous_distance = max(
            previous_distance,
            end
        )

        if distance_km <= end:

            break

    # --------------------------------------------------------
    # Safety fallback
    # --------------------------------------------------------

    if previous_distance < distance_km:

        last_rate = None

        if slabs:

            last_rate = slabs[-1].get(
                "rate_per_km"
            )

        if last_rate is not None:

            remaining = (
                distance_km
                - previous_distance
            )

            total += (
                remaining
                * float(last_rate)
            )

    return money(total)


# ============================================================
# DEFAULT FALLBACK FARE
# ============================================================

def calculate_default_fare(
    category_name: str,
    distance_km: float,
):

    """
    Emergency fallback only.

    Database fare rules should normally be used.
    """

    category = canonical_category_name(
        category_name
    )

    defaults = {

        "Auto Rickshaw": {
            "minimum_fare": 30.0,
            "minimum_distance": 1.5,
            "rate": 15.0,
        },

        "Motor Cab": {
            "minimum_fare": 200.0,
            "minimum_distance": 5.0,
            "rate": 18.0,
        },

        "Maxicab": {
            "minimum_fare": 225.0,
            "minimum_distance": 5.0,
            "rate": 20.0,
        },

    }

    rule = defaults.get(
        category
    )

    if not rule:
        return None

    if distance_km <= rule[
        "minimum_distance"
    ]:

        return money(
            rule["minimum_fare"]
        )

    extra_distance = (
        distance_km
        - rule["minimum_distance"]
    )

    fare = (
        rule["minimum_fare"]
        + (
            extra_distance
            * rule["rate"]
        )
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
    # Find category
    # --------------------------------------------------------

    category = find_category(
        request.category
    )

    if not category:

        canonical = canonical_category_name(
            request.category
        )

        raise HTTPException(
            status_code=404,
            detail={
                "message":
                    "Vehicle category not found",

                "requested":
                    request.category,

                "normalized":
                    canonical,
            }
        )

    category_id = category["id"]

    category_name = category["name"]

    # --------------------------------------------------------
    # Find energy source
    # --------------------------------------------------------

    energy = find_energy_source(
        request.energy_source
    )

    if request.energy_source and not energy:

        raise HTTPException(
            status_code=404,
            detail={
                "message":
                    "Energy source not found",

                "requested":
                    request.energy_source,
            }
        )

    energy_id = (
        energy["id"]
        if energy
        else None
    )

    # --------------------------------------------------------
    # Find vehicle
    # --------------------------------------------------------

    vehicle = find_vehicle(

        category_id=category_id,

        energy_source_id=energy_id,

        seating_capacity=
            request.seating_capacity,

        vehicle_id=
            request.vehicle_id,
    )

    # --------------------------------------------------------
    # Find fare rule
    # --------------------------------------------------------

    fare_rule = find_fare_rule(

        category_id=category_id,

        energy_source_id=energy_id,
    )

    fare = None

    calculation_method = None

    fare_rule_id = None

    # ========================================================
    # DATABASE FARE RULE
    # ========================================================

    if fare_rule:

        fare_rule_id = fare_rule.get(
            "id"
        )

        minimum_fare = fare_rule.get(
            "minimum_fare"
        )

        minimum_distance = fare_rule.get(
            "minimum_distance_km"
        )

        if (
            minimum_fare is not None
            and minimum_distance is not None
        ):

            minimum_fare = float(
                minimum_fare
            )

            minimum_distance = float(
                minimum_distance
            )

            # ------------------------------------------------
            # Find slabs
            # ------------------------------------------------

            slabs = find_fare_slabs(
                fare_rule_id
            )

            if slabs:

                fare = calculate_from_slabs(

                    distance_km=
                        request.distance_km,

                    minimum_fare=
                        minimum_fare,

                    minimum_distance_km=
                        minimum_distance,

                    slabs=slabs,
                )

                calculation_method = (
                    "database_fare_slabs"
                )

            else:

                # --------------------------------------------
                # No slabs: calculate using rule minimum
                # --------------------------------------------

                if (
                    request.distance_km
                    <= minimum_distance
                ):

                    fare = money(
                        minimum_fare
                    )

                else:

                    # Try rate from database if available
                    per_km = fare_rule.get(
                        "rate_per_km"
                    )

                    if per_km is None:

                        per_km = fare_rule.get(
                            "per_km_rate"
                        )

                    if per_km is not None:

                        extra_distance = (
                            request.distance_km
                            - minimum_distance
                        )

                        fare = money(
                            minimum_fare
                            + (
                                extra_distance
                                * float(per_km)
                            )
                        )

                        calculation_method = (
                            "database_fare_rule"
                        )

    # ========================================================
    # FALLBACK
    # ========================================================

    if fare is None:

        fare = calculate_default_fare(

            category_name=
                category_name,

            distance_km=
                request.distance_km,
        )

        if fare is not None:

            calculation_method = (
                "fallback_default"
            )

    # ========================================================
    # NO FARE AVAILABLE
    # ========================================================

    if fare is None:

        raise HTTPException(

            status_code=422,

            detail={
                "message":
                    "No fare rule is configured "
                    "for this vehicle category",

                "category":
                    category_name,

                "energy_source":
                    (
                        energy["name"]
                        if energy
                        else None
                    ),

                "distance_km":
                    request.distance_km,
            }
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "success": True,

        "calculation": {

            "category":
                category_name,

            "energy_source":
                (
                    energy["name"]
                    if energy
                    else None
                ),

            "distance_km":
                request.distance_km,

            "seating_capacity":
                request.seating_capacity,

            "vehicle":
                (
                    {
                        "id":
                            vehicle["id"],

                        "name":
                            vehicle["name"],

                        "seating_capacity":
                            vehicle[
                                "seating_capacity"
                            ],
                    }
                    if vehicle
                    else None
                ),

            "fare":
                fare,

            "currency":
                "INR",

            "calculation_method":
                calculation_method,

            "fare_rule_id":
                fare_rule_id,
        }
    }


# ============================================================
# SIMPLE GET FARE ENDPOINT
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

    return calculate_fare(
        request
    )


# ============================================================
# DEBUG CATEGORY
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

        "requested":
            category,

        "normalized":
            normalize_name(category),

        "canonical":
            canonical,

        "database_match":
            row,
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

                    result[table] = row[
                        "count"
                    ]

                except Exception as exc:

                    conn.rollback()

                    result[table] = {
                        "error": str(exc)
                    }

        return {

            "success": True,

            "tables":
                result,
        }

    finally:

        conn.close()


# ============================================================
# DEBUG FARE RULE
# ============================================================

@app.get("/api/debug/fare-rule")
def debug_fare_rule(
    category: str,
    energy_source: Optional[str] = None,
):

    category_row = find_category(
        category
    )

    if not category_row:

        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    energy_row = find_energy_source(
        energy_source
    )

    energy_id = (
        energy_row["id"]
        if energy_row
        else None
    )

    rule = find_fare_rule(

        category_id=
            category_row["id"],

        energy_source_id=
            energy_id,
    )

    if not rule:

        return {

            "success": True,

            "category":
                category_row["name"],

            "energy_source":
                (
                    energy_row["name"]
                    if energy_row
                    else None
                ),

            "fare_rule":
                None,

            "slabs":
                [],
        }

    slabs = find_fare_slabs(
        rule["id"]
    )

    return {

        "success": True,

        "category":
            category_row["name"],

        "energy_source":
            (
                energy_row["name"]
                if energy_row
                else None
            ),

        "fare_rule":
            rule,

        "slabs":
            slabs,
    }


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():

    print("=" * 60)

    print(
        "FARE KERALAM API STARTING"
    )

    print("=" * 60)

    if DATABASE_URL:

        print(
            "Database: CONFIGURED"
        )

        try:

            conn = psycopg2.connect(
                DATABASE_URL
            )

            conn.close()

            print(
                "Database connection: OK"
            )

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
# LOCAL ENTRY POINT
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