# ============================================================
# FARE KERALAM - MAIN API
# ============================================================
# Production-ready FastAPI backend
#
# Stack:
#   FastAPI
#   Supabase PostgreSQL
#   Render
#
# Current features:
#   - Health check
#   - Categories
#   - Energy sources
#   - Vehicles
#   - Vehicle options
#   - Database fare rules
#   - Progressive fare slabs
#   - Fare calculation
#   - Fare breakdown
#   - Database diagnostics
#
# Future-ready:
#   - Fuel price integration
#   - Operating-cost adjustment
#   - Cost index
#   - Historical fares
#   - Automated government/source updates
# ============================================================

import os
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
# FASTAPI
# ============================================================

app = FastAPI(
    title="Fare Keralam API",
    description=(
        "Kerala passenger transport fare calculation API "
        "with database-backed fare rules."
    ),
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
    Creates a PostgreSQL connection using DATABASE_URL.
    """

    if not DATABASE_URL:
        raise HTTPException(
            status_code=500,
            detail="Database is not configured"
        )

    try:
        return psycopg2.connect(
            DATABASE_URL,
            cursor_factory=psycopg2.extras.RealDictCursor,
            connect_timeout=10,
        )

    except Exception as exc:
        print("Database connection error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Unable to connect to database"
        )


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

        "status": (
            "healthy"
            if database_connected
            else "degraded"
        ),

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

    # --------------------------------------------------------
    # Category
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
    # Energy
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
    # Seating
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
# FARE REQUEST
# ============================================================

class FareCalculationRequest(BaseModel):

    category: str = Field(
        ...,
        description="Vehicle category"
    )

    energy_source: Optional[str] = Field(
        None,
        description=(
            "Petrol, Diesel, CNG, "
            "Electricity or Hybrid"
        )
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

    vehicle_id: Optional[int] = Field(
        None,
        gt=0
    )


# ============================================================
# MONEY
# ============================================================

def money(value: Any) -> float:

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
# FIND ENERGY
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

        vehicle = fetch_one(
            query,
            (vehicle_id,)
        )

        if vehicle is None:
            return None

        # Validate category
        if vehicle["category_id"] != category_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Selected vehicle does not belong "
                    "to the selected category"
                )
            )

        # Validate energy
        if (
            energy_source_id is not None
            and vehicle["energy_source_id"]
            != energy_source_id
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Selected vehicle does not use "
                    "the selected energy source"
                )
            )

        # Validate seating when supplied
        if (
            seating_capacity is not None
            and vehicle["seating_capacity"] is not None
            and vehicle["seating_capacity"]
            != seating_capacity
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Selected vehicle does not match "
                    "the selected seating capacity"
                )
            )

        return vehicle

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

    params = [category_id]

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
    energy_source_id: Optional[int] = None,
    seating_capacity: Optional[int] = None,
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

            ORDER BY
                effective_from DESC,
                id DESC

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
                "Energy-specific fare rule error:",
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

        ORDER BY
            effective_from DESC,
            id DESC

        LIMIT 1

    """

    try:

        return fetch_one(
            query,
            (category_id,)
        )

    except Exception as exc:

        print(
            "Category fare rule error:",
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
            "Fare slab lookup error:",
            exc
        )

        return []


# ============================================================
# SLAB CALCULATION
# ============================================================

def calculate_from_slabs(
    distance_km: float,
    minimum_fare: float,
    minimum_distance_km: float,
    slabs,
):

    minimum_fare = float(
        minimum_fare
    )

    minimum_distance_km = float(
        minimum_distance_km
    )

    # --------------------------------------------------------
    # Journey within minimum distance
    # --------------------------------------------------------

    if distance_km <= minimum_distance_km:

        return {
            "fare": minimum_fare,
            "base_fare": minimum_fare,
            "additional_fare": 0.0,
            "additional_distance_km": 0.0,
            "slab_breakdown": [],
        }

    # --------------------------------------------------------
    # No slabs
    # --------------------------------------------------------

    if not slabs:

        return {
            "fare": minimum_fare,
            "base_fare": minimum_fare,
            "additional_fare": 0.0,
            "additional_distance_km": (
                distance_km
                - minimum_distance_km
            ),
            "slab_breakdown": [],
        }

    total = minimum_fare

    additional_fare = 0.0

    slab_breakdown = []

    # --------------------------------------------------------
    # Calculate progressively
    # --------------------------------------------------------

    for slab in slabs:

        from_km = (
            float(slab["from_km"])
            if slab["from_km"] is not None
            else minimum_distance_km
        )

        to_km = (
            float(slab["to_km"])
            if slab["to_km"] is not None
            else None
        )

        rate = float(
            slab["rate_per_km"]
        )

        # Ignore slab that starts beyond journey
        if distance_km <= from_km:
            continue

        slab_start = max(
            from_km,
            minimum_distance_km
        )

        if to_km is None:

            slab_end = distance_km

        else:

            slab_end = min(
                distance_km,
                to_km
            )

        slab_distance = max(
            0.0,
            slab_end - slab_start
        )

        if slab_distance <= 0:
            continue

        slab_amount = (
            slab_distance * rate
        )

        additional_fare += slab_amount

        total += slab_amount

        slab_breakdown.append({

            "from_km": money(
                slab_start
            ),

            "to_km": money(
                slab_end
            ),

            "distance_km": money(
                slab_distance
            ),

            "rate_per_km": money(
                rate
            ),

            "amount": money(
                slab_amount
            ),
        })

    # --------------------------------------------------------
    # Safety:
    # If slabs didn't cover the entire journey,
    # do not silently undercharge.
    # --------------------------------------------------------

    covered_distance = sum(
        item["distance_km"]
        for item in slab_breakdown
    )

    required_distance = max(
        0.0,
        distance_km - minimum_distance_km
    )

    uncovered_distance = max(
        0.0,
        required_distance - covered_distance
    )

    if uncovered_distance > 0:

        # Use the last available slab rate
        # for the uncovered distance.

        if slabs:

            last_rate = float(
                slabs[-1]["rate_per_km"]
            )

            extra_amount = (
                uncovered_distance
                * last_rate
            )

            additional_fare += (
                extra_amount
            )

            total += extra_amount

            slab_breakdown.append({

                "from_km": money(
                    distance_km
                    - uncovered_distance
                ),

                "to_km": money(
                    distance_km
                ),

                "distance_km": money(
                    uncovered_distance
                ),

                "rate_per_km": money(
                    last_rate
                ),

                "amount": money(
                    extra_amount
                ),

                "continuation": True,
            })

    return {

        "fare": total,

        "base_fare": minimum_fare,

        "additional_fare": additional_fare,

        "additional_distance_km": (
            required_distance
        ),

        "slab_breakdown": slab_breakdown,
    }


# ============================================================
# FALLBACK FARE
# ============================================================
#
# IMPORTANT:
# These are NOT presented as current government rules.
# They are only emergency estimates when no active
# database fare rule exists.
#
# The real production system should eventually have
# database rules for every supported category.
# ============================================================

def fallback_fare(
    category: str,
    distance_km: float,
):

    category_normalized = normalize_name(
        category
    )

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
    # Maxicab
    # --------------------------------------------------------

    elif category_normalized == "maxicab":

        minimum_fare = 200.0
        minimum_distance = 5.0
        rate = 20.0

    # --------------------------------------------------------
    # Contract Carriage
    # --------------------------------------------------------

    elif category_normalized == "contract carriage":

        minimum_fare = 200.0
        minimum_distance = 5.0
        rate = 20.0

    # --------------------------------------------------------
    # Stage Carriage
    # --------------------------------------------------------

    elif category_normalized == "stage carriage":

        minimum_fare = 20.0
        minimum_distance = 1.0
        rate = 10.0

    else:

        minimum_fare = 30.0
        minimum_distance = 1.5
        rate = 15.0

    if distance_km <= minimum_distance:

        fare = minimum_fare

    else:

        fare = (
            minimum_fare
            + (
                distance_km
                - minimum_distance
            ) * rate
        )

    return {

        "fare": fare,

        "base_fare": minimum_fare,

        "additional_fare": max(
            0.0,
            fare - minimum_fare
        ),

        "additional_distance_km": max(
            0.0,
            distance_km
            - minimum_distance
        ),

        "rate_per_km": rate,
    }


# ============================================================
# FARE CALCULATION
# ============================================================

@app.post("/api/fare/calculate")
def calculate_fare(
    request: FareCalculationRequest
):

    # ========================================================
    # 1. CATEGORY
    # ========================================================

    category = find_category(
        request.category
    )

    if not category:

        raise HTTPException(

            status_code=404,

            detail={

                "message":
                    "Vehicle category not found",

                "requested":
                    request.category,

                "normalized":
                    normalize_name(
                        request.category
                    ),
            }
        )

    category_id = category["id"]

    # ========================================================
    # 2. ENERGY
    # ========================================================

    energy = find_energy_source(
        request.energy_source
    )

    if (
        request.energy_source
        and not energy
    ):

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

    # ========================================================
    # 3. VEHICLE
    # ========================================================

    vehicle = find_vehicle(

        category_id=category_id,

        energy_source_id=energy_id,

        seating_capacity=
            request.seating_capacity,

        vehicle_id=
            request.vehicle_id,
    )

    # ========================================================
    # 4. FARE RULE
    # ========================================================

    fare_rule = find_fare_rule(

        category_id=category_id,

        energy_source_id=energy_id,

        seating_capacity=
            request.seating_capacity,
    )

    # ========================================================
    # 5. DATABASE FARE
    # ========================================================

    if fare_rule:

        minimum_fare = float(
            fare_rule["minimum_fare"]
        )

        minimum_distance = float(
            fare_rule[
                "minimum_distance_km"
            ]
        )

        slabs = find_fare_slabs(
            fare_rule["id"]
        )

        result = calculate_from_slabs(

            distance_km=
                request.distance_km,

            minimum_fare=
                minimum_fare,

            minimum_distance_km=
                minimum_distance,

            slabs=slabs,
        )

        return {

            "success": True,

            "calculation": {

                "category":
                    category["name"],

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
                    vehicle,

                "fare":
                    money(
                        result["fare"]
                    ),

                "currency":
                    "INR",

                "calculation_method":
                    "database_fare_rule",

                "fare_rule_id":
                    fare_rule["id"],

                "government_reference":
                    fare_rule.get(
                        "government_reference"
                    ),

                "minimum_fare":
                    money(
                        minimum_fare
                    ),

                "minimum_distance_km":
                    minimum_distance,

                "additional_distance_km":
                    money(
                        result[
                            "additional_distance_km"
                        ]
                    ),

                "additional_fare":
                    money(
                        result[
                            "additional_fare"
                        ]
                    ),

                "slab_breakdown":
                    result[
                        "slab_breakdown"
                    ],

                "fare_source":
                    "database",
            }
        }

    # ========================================================
    # 6. FALLBACK
    # ========================================================

    fallback = fallback_fare(

        category=category["name"],

        distance_km=
            request.distance_km,
    )

    return {

        "success": True,

        "calculation": {

            "category":
                category["name"],

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
                vehicle,

            "fare":
                money(
                    fallback["fare"]
                ),

            "currency":
                "INR",

            "calculation_method":
                "fallback_estimate",

            "fare_rule_id":
                None,

            "minimum_fare":
                money(
                    fallback["base_fare"]
                ),

            "additional_distance_km":
                money(
                    fallback[
                        "additional_distance_km"
                    ]
                ),

            "additional_fare":
                money(
                    fallback[
                        "additional_fare"
                    ]
                ),

            "rate_per_km":
                money(
                    fallback[
                        "rate_per_km"
                    ]
                ),

            "fare_source":
                "fallback_estimate",

            "warning":
                (
                    "No active database fare rule "
                    "was found for this category. "
                    "This result is an estimate and "
                    "should not be treated as an "
                    "official government fare."
                ),
        }
    }

# ============================================================
# COST & FUEL PRICE ENGINE
# ============================================================

from datetime import date
from pydantic import BaseModel, Field


# ------------------------------------------------------------
# COST CATEGORY LOOKUP
# ------------------------------------------------------------

def find_cost_category(name: str):
    query = """
        SELECT
            id,
            name,
            description,
            active
        FROM cost_categories
        WHERE active = TRUE
          AND LOWER(name) = LOWER(%s)
        LIMIT 1
    """
    return fetch_one(query, (name.strip(),))


# ------------------------------------------------------------
# DATA SOURCE LOOKUP
# ------------------------------------------------------------

def find_data_source(source_name: str):
    query = """
        SELECT
            id,
            name,
            organization,
            url,
            data_type,
            source_level,
            verification_status
        FROM data_sources
        WHERE LOWER(name) = LOWER(%s)
        LIMIT 1
    """
    return fetch_one(query, (source_name.strip(),))


# ============================================================
# GET CURRENT FUEL / COST DATA
# ============================================================

@app.get("/api/costs")
def get_current_costs(
    energy_source: Optional[str] = None,
    location: str = "Kerala"
):
    """
    Returns the latest verified operating-cost records.
    """

    query = """
        SELECT
            cd.id,
            cc.name AS cost_category,
            es.name AS energy_source,
            cd.value,
            cd.unit,
            cd.location,
            cd.district,
            cd.effective_date,
            ds.name AS source,
            ds.organization,
            ds.url AS source_url,
            cd.source_reference,
            cd.verification_status,
            cd.retrieved_at
        FROM cost_data cd

        INNER JOIN cost_categories cc
            ON cc.id = cd.cost_category_id

        LEFT JOIN energy_sources es
            ON es.id = cd.energy_source_id

        LEFT JOIN data_sources ds
            ON ds.id = cd.source_id

        WHERE cd.location = %s
          AND cd.verification_status = 'verified'
    """

    params = [location]

    if energy_source:
        query += """
            AND LOWER(es.name) = LOWER(%s)
        """
        params.append(energy_source.strip())

    query += """
        ORDER BY
            cd.effective_date DESC,
            cd.id DESC
    """

    try:
        rows = fetch_all(query, params)

        return {
            "success": True,
            "count": len(rows),
            "costs": rows,
        }

    except Exception as exc:
        print("Cost data error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Unable to load cost data"
        )


# ============================================================
# PRICE HISTORY
# ============================================================

@app.get("/api/prices")
def get_price_history(
    energy_source: Optional[str] = None,
    location: str = "Kerala",
    limit: int = 100
):
    """
    Returns historical fuel/energy prices.
    """

    limit = max(1, min(limit, 500))

    query = """
        SELECT
            ph.id,
            cc.name AS cost_category,
            es.name AS energy_source,
            ph.value,
            ph.unit,
            ph.location,
            ph.district,
            ph.price_date,
            ds.name AS source,
            ds.organization,
            ds.url AS source_url,
            ph.source_reference,
            ph.retrieved_at
        FROM price_history ph

        INNER JOIN cost_categories cc
            ON cc.id = ph.cost_category_id

        LEFT JOIN energy_sources es
            ON es.id = ph.energy_source_id

        LEFT JOIN data_sources ds
            ON ds.id = ph.source_id

        WHERE ph.location = %s
    """

    params = [location]

    if energy_source:
        query += """
            AND LOWER(es.name) = LOWER(%s)
        """
        params.append(energy_source.strip())

    query += """
        ORDER BY ph.price_date DESC, ph.id DESC
        LIMIT %s
    """

    params.append(limit)

    try:
        rows = fetch_all(query, params)

        return {
            "success": True,
            "count": len(rows),
            "prices": rows,
        }

    except Exception as exc:
        print("Price history error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Unable to load price history"
        )


# ============================================================
# CURRENT PRICE FOR ONE ENERGY SOURCE
# ============================================================

@app.get("/api/prices/latest")
def get_latest_price(
    energy_source: str,
    location: str = "Kerala"
):
    """
    Returns the latest available verified price.
    """

    query = """
        SELECT
            ph.id,
            cc.name AS cost_category,
            es.name AS energy_source,
            ph.value,
            ph.unit,
            ph.location,
            ph.district,
            ph.price_date,
            ds.name AS source,
            ds.organization,
            ds.url AS source_url,
            ph.source_reference,
            ph.retrieved_at
        FROM price_history ph

        INNER JOIN cost_categories cc
            ON cc.id = ph.cost_category_id

        INNER JOIN energy_sources es
            ON es.id = ph.energy_source_id

        LEFT JOIN data_sources ds
            ON ds.id = ph.source_id

        WHERE LOWER(es.name) = LOWER(%s)
          AND ph.location = %s

        ORDER BY
            ph.price_date DESC,
            ph.id DESC

        LIMIT 1
    """

    try:
        row = fetch_one(
            query,
            (
                energy_source.strip(),
                location
            )
        )

        if not row:
            return {
                "success": True,
                "available": False,
                "price": None,
            }

        return {
            "success": True,
            "available": True,
            "price": row,
        }

    except Exception as exc:
        print("Latest price error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Unable to load latest price"
        )


# ============================================================
# COST INDEX
# ============================================================

@app.get("/api/cost-index")
def get_cost_index(
    cost_category: Optional[str] = None,
    location: str = "Kerala"
):
    """
    Returns the latest operating-cost index.
    """

    query = """
        SELECT
            cih.id,
            cc.name AS cost_category,
            cih.index_value,
            cih.reference_period,
            cih.location,
            ds.name AS source,
            ds.organization,
            cih.notes,
            cih.created_at
        FROM cost_index_history cih

        INNER JOIN cost_categories cc
            ON cc.id = cih.cost_category_id

        LEFT JOIN data_sources ds
            ON ds.id = cih.source_id

        WHERE cih.location = %s
    """

    params = [location]

    if cost_category:
        query += """
            AND LOWER(cc.name) = LOWER(%s)
        """
        params.append(cost_category.strip())

    query += """
        ORDER BY
            cih.reference_period DESC,
            cih.id DESC
    """

    try:
        rows = fetch_all(query, params)

        return {
            "success": True,
            "count": len(rows),
            "indices": rows,
        }

    except Exception as exc:
        print("Cost index error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Unable to load cost index"
        )


# ============================================================
# MANUAL PRICE RECORD
# ============================================================

class PriceRecordRequest(BaseModel):
    energy_source: str = Field(..., min_length=1)
    value: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)
    price_date: date
    source_name: str = Field(..., min_length=1)
    location: str = "Kerala"
    district: Optional[str] = None
    source_reference: Optional[str] = None


@app.post("/api/prices")
def record_price(request: PriceRecordRequest):
    """
    Adds a manually verified price record.

    This endpoint is intended for trusted/admin use.
    It does NOT automatically declare the data official.
    """

    energy = find_energy_source(
        request.energy_source
    )

    if not energy:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Energy source not found",
                "requested": request.energy_source,
            }
        )

    source = find_data_source(
        request.source_name
    )

    if not source:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Data source not found",
                "requested": request.source_name,
            }
        )

    # Find a suitable cost category.
    cost_category = find_cost_category("Fuel")

    if not cost_category:
        raise HTTPException(
            status_code=500,
            detail="Fuel cost category is not configured"
        )

    query = """
        INSERT INTO price_history
        (
            cost_category_id,
            energy_source_id,
            value,
            unit,
            location,
            district,
            price_date,
            source_id,
            source_reference,
            retrieved_at
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            NOW()
        )
        RETURNING
            id,
            value,
            unit,
            location,
            district,
            price_date,
            source_reference,
            retrieved_at
    """

    try:
        row = fetch_one(
            query,
            (
                cost_category["id"],
                energy["id"],
                request.value,
                request.unit,
                request.location,
                request.district,
                request.price_date,
                source["id"],
                request.source_reference,
            )
        )

        return {
            "success": True,
            "message": "Price record added",
            "price": row,
        }

    except Exception as exc:
        print("Price insert error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Unable to record price"
        )


# ============================================================
# COST DATA RECORD
# ============================================================

class CostRecordRequest(BaseModel):
    cost_category: str = Field(..., min_length=1)
    energy_source: Optional[str] = None
    value: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)
    effective_date: date
    source_name: str = Field(..., min_length=1)
    location: str = "Kerala"
    district: Optional[str] = None
    source_reference: Optional[str] = None
    verification_status: str = "pending"


@app.post("/api/costs")
def record_cost(request: CostRecordRequest):

    if request.verification_status not in {
        "pending",
        "verified",
        "rejected"
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification status"
        )

    category = find_cost_category(
        request.cost_category
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Cost category not found",
                "requested": request.cost_category,
            }
        )

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

    source = find_data_source(
        request.source_name
    )

    if not source:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Data source not found",
                "requested": request.source_name,
            }
        )

    query = """
        INSERT INTO cost_data
        (
            cost_category_id,
            energy_source_id,
            value,
            unit,
            location,
            district,
            effective_date,
            source_id,
            source_reference,
            retrieved_at,
            verification_status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            NOW(),
            %s
        )
        RETURNING
            id,
            value,
            unit,
            location,
            district,
            effective_date,
            verification_status,
            retrieved_at
    """

    try:
        row = fetch_one(
            query,
            (
                category["id"],
                energy["id"] if energy else None,
                request.value,
                request.unit,
                request.location,
                request.district,
                request.effective_date,
                source["id"],
                request.source_reference,
                request.verification_status,
            )
        )

        return {
            "success": True,
            "message": "Cost record added",
            "cost": row,
        }

    except Exception as exc:
        print("Cost insert error:", exc)

        raise HTTPException(
            status_code=500,
            detail="Unable to record cost"
        )


# ============================================================
# OPERATING COST ESTIMATE
# ============================================================

@app.get("/api/operating-cost")
def operating_cost(
    vehicle_id: int,
    distance_km: float = 1.0
):
    """
    Estimates direct fuel/energy cost for a vehicle.

    This is deliberately separate from the official fare.
    """

    if distance_km <= 0:
        raise HTTPException(
            status_code=400,
            detail="distance_km must be greater than zero"
        )

    vehicle_query = """
        SELECT
            v.id,
            v.name,
            v.category_id,
            v.energy_source_id,
            v.seating_capacity,
            v.efficiency,
            v.efficiency_unit,
            es.name AS energy_source
        FROM vehicles v

        LEFT JOIN energy_sources es
            ON es.id = v.energy_source_id

        WHERE v.id = %s
          AND v.active = TRUE

        LIMIT 1
    """

    vehicle = fetch_one(
        vehicle_query,
        (vehicle_id,)
    )

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    if not vehicle["efficiency"]:
        return {
            "success": True,
            "available": False,
            "reason": "Vehicle efficiency is not configured",
            "vehicle": vehicle,
        }

    if not vehicle["energy_source_id"]:
        return {
            "success": True,
            "available": False,
            "reason": "Vehicle energy source is not configured",
            "vehicle": vehicle,
        }

    price_query = """
        SELECT
            ph.value,
            ph.unit,
            ph.price_date,
            ph.location,
            ds.name AS source,
            ds.url AS source_url
        FROM price_history ph

        LEFT JOIN data_sources ds
            ON ds.id = ph.source_id

        WHERE ph.energy_source_id = %s
          AND ph.location = 'Kerala'

        ORDER BY
            ph.price_date DESC,
            ph.id DESC

        LIMIT 1
    """

    price = fetch_one(
        price_query,
        (vehicle["energy_source_id"],)
    )

    if not price:
        return {
            "success": True,
            "available": False,
            "reason": "No current energy price is available",
            "vehicle": vehicle,
        }

    efficiency = float(vehicle["efficiency"])
    energy_price = float(price["value"])

    efficiency_unit = (
        vehicle["efficiency_unit"] or ""
    ).lower()

    # --------------------------------------------------------
    # km per litre / km per unit
    # --------------------------------------------------------
    if "km" in efficiency_unit and (
        "l" in efficiency_unit
        or "unit" in efficiency_unit
    ):
        energy_used = distance_km / efficiency

    # --------------------------------------------------------
    # litre / 100 km
    # --------------------------------------------------------
    elif "l/100" in efficiency_unit:
        energy_used = (
            distance_km * efficiency / 100
        )

    else:
        return {
            "success": True,
            "available": False,
            "reason": (
                "Unsupported efficiency unit: "
                + str(vehicle["efficiency_unit"])
            ),
            "vehicle": vehicle,
        }

    direct_energy_cost = (
        energy_used * energy_price
    )

    return {
        "success": True,
        "available": True,
        "vehicle": vehicle,
        "distance_km": distance_km,
        "efficiency": efficiency,
        "efficiency_unit": vehicle["efficiency_unit"],
        "energy_used": round(
            energy_used,
            4
        ),
        "energy_price": money(
            energy_price
        ),
        "energy_price_unit": price["unit"],
        "direct_energy_cost": money(
            direct_energy_cost
        ),
        "price_date": price["price_date"],
        "source": price["source"],
        "source_url": price["source_url"],
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
                        f"""
                        SELECT COUNT(*) AS count
                        FROM {table}
                        """
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