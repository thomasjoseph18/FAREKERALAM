# ============================================================
# FARE KERALAM - MAIN API
# ============================================================
# FastAPI backend
# Supabase PostgreSQL
# Render deployment
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
# FASTAPI
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
# DATABASE
# ============================================================

def get_connection():
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


def fetch_one(query, params=()):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    finally:
        conn.close()


def fetch_all(query, params=()):
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


def canonical_category_name(category: Optional[str]):

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
# FARE REQUEST
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
# MONEY ROUNDING
# ============================================================

def money(value):

    amount = Decimal(str(value))

    rounded = amount.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    return float(rounded)


# ============================================================
# FIND CATEGORY
# ============================================================

def find_category(category_name):

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

def find_energy_source(energy_name):

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
    category_id,
    energy_source_id,
    seating_capacity,
    vehicle_id
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
# FIND FARE RULE
# ============================================================
# IMPORTANT:
# Your Supabase table uses:
#
#     category_id
#
# NOT:
#
#     vehicle_category_id
#
# ============================================================

def find_fare_rule(
    category_id,
    energy_source_id=None,
    seating_capacity=None
):

    # --------------------------------------------------------
    # 1. Energy-specific rule
    # --------------------------------------------------------

    if energy_source_id is not None:

        query = """
            SELECT *
            FROM fare_rules
            WHERE category_id = %s
              AND energy_source_id = %s
              AND status = 'active'
              AND effective_from <= CURRENT_DATE
              AND (
                    effective_to IS NULL
                    OR effective_to >= CURRENT_DATE
                  )
            ORDER BY effective_from DESC, id DESC
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
    # 2. Category-only rule
    # --------------------------------------------------------

    query = """
        SELECT *
        FROM fare_rules
        WHERE category_id = %s
          AND energy_source_id IS NULL
          AND status = 'active'
          AND effective_from <= CURRENT_DATE
          AND (
                effective_to IS NULL
                OR effective_to >= CURRENT_DATE
              )
        ORDER BY effective_from DESC, id DESC
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

def find_fare_slabs(fare_rule_id):

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
# CALCULATE USING SLABS
# ============================================================

def calculate_from_slabs(
    distance_km,
    minimum_fare,
    minimum_distance_km,
    slabs
):

    # --------------------------------------------------------
    # No slabs
    # --------------------------------------------------------

    if not slabs:

        if distance_km <= minimum_distance_km:
            return minimum_fare

        return (
            minimum_fare
            + (
                distance_km - minimum_distance_km
            ) * 0
        )

    total = minimum_fare

    # Distance already covered by minimum fare
    remaining_distance = max(
        0.0,
        distance_km - minimum_distance_km
    )

    current_distance = minimum_distance_km

    for slab in slabs:

        from_km = float(
            slab["from_km"]
            if slab["from_km"] is not None
            else current_distance
        )

        to_km = (
            float(slab["to_km"])
            if slab["to_km"] is not None
            else None
        )

        rate = float(
            slab["rate_per_km"]
        )

        # ----------------------------------------------------
        # Slab begins after the requested distance
        # ----------------------------------------------------

        if distance_km <= from_km:
            continue

        # ----------------------------------------------------
        # Determine slab distance
        # ----------------------------------------------------

        slab_start = max(
            from_km,
            minimum_distance_km
        )

        if to_km is None:

            slab_distance = max(
                0.0,
                distance_km - slab_start
            )

        else:

            slab_end = min(
                distance_km,
                to_km
            )

            slab_distance = max(
                0.0,
                slab_end - slab_start
            )

        total += slab_distance * rate

        current_distance = (
            to_km
            if to_km is not None
            else distance_km
        )

    return total


# ============================================================
# DEFAULT FALLBACK
# ============================================================

def fallback_fare(
    category,
    distance_km
):

    category_normalized = normalize_name(category)

    # --------------------------------------------------------
    # Auto Rickshaw
    # --------------------------------------------------------

    if category_normalized == "auto rickshaw":

        minimum_fare = 30.0
        minimum_distance = 1.5
        rate = 15.0

    # --------------------------------------------------------
    # Motor Cab
    # --------------------------------------------------------

    elif category_normalized == "motor cab":

        minimum_fare = 200.0
        minimum_distance = 5.0
        rate = 18.0

    # --------------------------------------------------------
    # Generic fallback
    # --------------------------------------------------------

    else:

        minimum_fare = 30.0
        minimum_distance = 1.5
        rate = 15.0

    if distance_km <= minimum_distance:
        return minimum_fare

    return (
        minimum_fare
        + (
            distance_km - minimum_distance
        ) * rate
    )


# ============================================================
# FARE CALCULATION
# ============================================================

@app.post("/api/fare/calculate")
def calculate_fare(
    request: FareCalculationRequest
):

    # --------------------------------------------------------
    # Validate category
    # --------------------------------------------------------

    category = find_category(
        request.category
    )

    if not category:

        raise HTTPException(
            status_code=404,
            detail={
                "message": "Vehicle category not found",
                "requested": request.category,
                "normalized": normalize_name(
                    request.category
                ),
            }
        )

    category_id = category["id"]

    # --------------------------------------------------------
    # Energy source
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
    # Vehicle
    # --------------------------------------------------------

    vehicle = find_vehicle(
        category_id=category_id,
        energy_source_id=energy_id,
        seating_capacity=request.seating_capacity,
        vehicle_id=request.vehicle_id,
    )

    # --------------------------------------------------------
    # Fare rule
    # --------------------------------------------------------

    fare_rule = find_fare_rule(
        category_id=category_id,
        energy_source_id=energy_id,
        seating_capacity=request.seating_capacity,
    )

    # ========================================================
    # DATABASE FARE CALCULATION
    # ========================================================

    if fare_rule:

        minimum_fare = float(
            fare_rule["minimum_fare"]
        )

        minimum_distance = float(
            fare_rule["minimum_distance_km"]
        )

        slabs = find_fare_slabs(
            fare_rule["id"]
        )

        fare = calculate_from_slabs(
            distance_km=request.distance_km,
            minimum_fare=minimum_fare,
            minimum_distance_km=minimum_distance,
            slabs=slabs,
        )

        return {
            "success": True,

            "calculation": {
                "category": category["name"],

                "energy_source": (
                    energy["name"]
                    if energy
                    else None
                ),

                "distance_km": request.distance_km,

                "seating_capacity":
                    request.seating_capacity,

                "vehicle": vehicle,

                "fare": money(fare),

                "currency": "INR",

                "calculation_method":
                    "database_fare_rule",

                "fare_rule_id":
                    fare_rule["id"],
            }
        }

    # ========================================================
    # FALLBACK
    # ========================================================

    fare = fallback_fare(
        category=category["name"],
        distance_km=request.distance_km,
    )

    return {
        "success": True,

        "calculation": {
            "category": category["name"],

            "energy_source": (
                energy["name"]
                if energy
                else None
            ),

            "distance_km":
                request.distance_km,

            "seating_capacity":
                request.seating_capacity,

            "vehicle": vehicle,

            "fare": money(fare),

            "currency": "INR",

            "calculation_method":
                "fallback_default",

            "fare_rule_id": None,
        }
    }


# ============================================================
# DATABASE DEBUG
# ============================================================

@app.get("/api/debug/database")
def debug_database():

    tables = {}

    table_names = [
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

            for table in table_names:

                try:

                    cursor.execute(
                        f"SELECT COUNT(*) AS count FROM {table}"
                    )

                    row = cursor.fetchone()

                    tables[table] = row["count"]

                except Exception as exc:

                    print(
                        f"Table {table} error:",
                        exc
                    )

                    tables[table] = 0

        return {
            "success": True,
            "tables": tables,
        }

    finally:

        conn.close()