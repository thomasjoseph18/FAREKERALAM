import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client, Client


# ============================================================
# APP CONFIGURATION
# ============================================================

app = FastAPI(
    title="Fare Keralam API",
    description="Kerala passenger transport fare calculation and revision API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SUPABASE CONFIGURATION
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )
    except Exception:
        supabase = None


# ============================================================
# MODELS
# ============================================================

class FareCalculateRequest(BaseModel):
    category_id: int
    distance_km: float = Field(gt=0)
    energy_source_id: Optional[int] = None
    seating_capacity: Optional[int] = None


class FuelPriceRequest(BaseModel):
    energy_source_id: int
    price: float = Field(ge=0)
    effective_from: Optional[str] = None
    source_id: Optional[int] = None
    notes: Optional[str] = None


# ============================================================
# BASIC HELPERS
# ============================================================

def require_database():
    if supabase is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured"
        )


def get_category(category_id: int):
    require_database()

    result = (
        supabase
        .table("vehicle_categories")
        .select("*")
        .eq("id", category_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Vehicle category not found"
        )

    return result.data[0]


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "success": True,
        "name": "Fare Keralam API",
        "version": "1.0.0",
        "status": "running"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():
    database_configured = supabase is not None

    return {
        "status": "healthy",
        "database_configured": database_configured
    }


# ============================================================
# VEHICLE CATEGORIES
# ============================================================

@app.get("/api/categories")
def get_categories():
    require_database()

    result = (
        supabase
        .table("vehicle_categories")
        .select("*")
        .order("id")
        .execute()
    )

    return {
        "success": True,
        "count": len(result.data or []),
        "categories": result.data or []
    }


# ============================================================
# ENERGY SOURCES
# ============================================================

@app.get("/api/energy-sources")
def get_energy_sources():
    require_database()

    result = (
        supabase
        .table("energy_sources")
        .select("*")
        .order("id")
        .execute()
    )

    return {
        "success": True,
        "count": len(result.data or []),
        "energy_sources": result.data or []
    }


# ============================================================
# VEHICLES
# ============================================================

@app.get("/api/vehicles")
def get_vehicles(
    category_id: Optional[int] = None,
    energy_source_id: Optional[int] = None,
    seating_capacity: Optional[int] = None
):
    require_database()

    query = (
        supabase
        .table("vehicles")
        .select("*")
        .eq("active", True)
    )

    if category_id is not None:
        query = query.eq("category_id", category_id)

    if energy_source_id is not None:
        query = query.eq(
            "energy_source_id",
            energy_source_id
        )

    if seating_capacity is not None:
        query = query.eq(
            "seating_capacity",
            seating_capacity
        )

    result = query.order("id").execute()

    return {
        "success": True,
        "count": len(result.data or []),
        "vehicles": result.data or []
    }


# ============================================================
# VEHICLE OPTIONS
#
# Government category
#       ↓
# Fuel / energy
#       ↓
# Seating capacity
#
# This endpoint derives the options directly from vehicles.
# ============================================================

@app.get("/api/vehicle-options")
def get_vehicle_options():
    require_database()

    try:
        result = (
            supabase
            .table("vehicles")
            .select(
                """
                id,
                name,
                seating_capacity,
                category_id,
                energy_source_id,
                vehicle_categories!inner(id,name),
                energy_sources!inner(id,name)
                """
            )
            .eq("active", True)
            .execute()
        )

        categories = {}

        for vehicle in result.data or []:

            category_data = vehicle.get(
                "vehicle_categories"
            )

            energy_data = vehicle.get(
                "energy_sources"
            )

            if not category_data or not energy_data:
                continue

            category_name = category_data.get("name")
            energy_name = energy_data.get("name")

            if not category_name or not energy_name:
                continue

            if category_name not in categories:
                categories[category_name] = {}

            if energy_name not in categories[category_name]:
                categories[category_name][energy_name] = []

            seating = vehicle.get("seating_capacity")

            if seating is not None:
                if seating not in categories[category_name][energy_name]:
                    categories[category_name][energy_name].append(
                        seating
                    )

        # Sort seating capacities
        for category in categories:
            for energy in categories[category]:
                categories[category][energy].sort()

        return {
            "success": True,
            "categories": categories
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build vehicle options: {str(e)}"
        )


# ============================================================
# VEHICLES BY CATEGORY
# ============================================================

@app.get("/api/categories/{category_id}/vehicles")
def get_category_vehicles(category_id: int):
    require_database()

    category = get_category(category_id)

    result = (
        supabase
        .table("vehicles")
        .select("*")
        .eq("category_id", category_id)
        .eq("active", True)
        .order("seating_capacity")
        .order("id")
        .execute()
    )

    return {
        "success": True,
        "category": category,
        "count": len(result.data or []),
        "vehicles": result.data or []
    }


# ============================================================
# FARE RULES
# ============================================================

@app.get("/api/fare-rules")
def get_fare_rules(
    category_id: Optional[int] = None,
    energy_source_id: Optional[int] = None,
    status: Optional[str] = None
):
    require_database()

    query = (
        supabase
        .table("fare_rules")
        .select("*")
    )

    if category_id is not None:
        query = query.eq(
            "category_id",
            category_id
        )

    if energy_source_id is not None:
        query = query.eq(
            "energy_source_id",
            energy_source_id
        )

    if status is not None:
        query = query.eq(
            "status",
            status
        )

    result = query.order("id").execute()

    return {
        "success": True,
        "count": len(result.data or []),
        "fare_rules": result.data or []
    }


# ============================================================
# FARE SLABS
# ============================================================

@app.get("/api/fare-slabs")
def get_fare_slabs(
    fare_rule_id: Optional[int] = None
):
    require_database()

    query = (
        supabase
        .table("fare_slabs")
        .select("*")
    )

    if fare_rule_id is not None:
        query = query.eq(
            "fare_rule_id",
            fare_rule_id
        )

    result = (
        query
        .order("fare_rule_id")
        .order("from_km")
        .execute()
    )

    return {
        "success": True,
        "count": len(result.data or []),
        "fare_slabs": result.data or []
    }


# ============================================================
# FARE CALCULATION
# ============================================================

@app.post("/api/fare/calculate")
def calculate_fare(request: FareCalculateRequest):
    require_database()

    category = get_category(request.category_id)

    # --------------------------------------------------------
    # Find applicable fare rules
    # --------------------------------------------------------

    query = (
        supabase
        .table("fare_rules")
        .select("*")
        .eq("category_id", request.category_id)
        .eq("status", "active")
    )

    if request.energy_source_id is not None:
        query = query.or_(
            f"energy_source_id.eq.{request.energy_source_id},"
            "energy_source_id.is.null"
        )

    rules_result = query.order("id").execute()

    rules = rules_result.data or []

    if not rules:
        raise HTTPException(
            status_code=404,
            detail="No active fare rule found for this vehicle category"
        )

    # --------------------------------------------------------
    # Select first applicable rule
    # --------------------------------------------------------

    rule = None

    for candidate in rules:

        minimum_distance = float(
            candidate.get("minimum_distance_km") or 0
        )

        if request.distance_km >= minimum_distance:
            rule = candidate
            break

    if rule is None:
        rule = rules[0]

    fare_rule_id = rule["id"]

    minimum_fare = float(
        rule["minimum_fare"]
    )

    minimum_distance = float(
        rule["minimum_distance_km"]
    )

    # --------------------------------------------------------
    # Get slabs
    # --------------------------------------------------------

    slabs_result = (
        supabase
        .table("fare_slabs")
        .select("*")
        .eq("fare_rule_id", fare_rule_id)
        .order("from_km")
        .execute()
    )

    slabs = slabs_result.data or []

    # --------------------------------------------------------
    # Calculate base fare
    # --------------------------------------------------------

    distance = request.distance_km

    if distance <= minimum_distance:
        base_fare = minimum_fare

    else:
        base_fare = minimum_fare

        remaining_distance = distance - minimum_distance

        for slab in slabs:

            from_km = float(
                slab.get("from_km") or 0
            )

            to_km = slab.get("to_km")

            rate = float(
                slab.get("rate_per_km") or 0
            )

            if to_km is None:

                if distance > from_km:
                    slab_distance = distance - max(
                        from_km,
                        minimum_distance
                    )

                    if slab_distance > 0:
                        base_fare += (
                            slab_distance * rate
                        )

                    remaining_distance = 0

                break

            to_km = float(to_km)

            if distance <= from_km:
                continue

            slab_start = max(
                from_km,
                minimum_distance
            )

            slab_end = min(
                distance,
                to_km
            )

            slab_distance = slab_end - slab_start

            if slab_distance > 0:
                base_fare += (
                    slab_distance * rate
                )

            remaining_distance -= max(
                0,
                slab_distance
            )

            if distance <= to_km:
                break

    # --------------------------------------------------------
    # Round final base fare
    # --------------------------------------------------------

    base_fare = round(
        base_fare,
        2
    )

    return {
        "success": True,
        "category": category.get("name"),
        "category_id": request.category_id,
        "energy_source_id": request.energy_source_id,
        "seating_capacity": request.seating_capacity,
        "distance_km": request.distance_km,
        "fare_rule_id": fare_rule_id,
        "minimum_fare": minimum_fare,
        "minimum_distance_km": minimum_distance,
        "base_fare": base_fare,
        "final_fare": base_fare,
        "fare_revision_applied": False,
        "message": "Fare calculated using the active government fare rule."
    }


# ============================================================
# CURRENT FUEL PRICES
# ============================================================

@app.get("/api/fuel/current")
def get_current_fuel_prices():
    require_database()

    result = (
        supabase
        .table("current_fuel_prices")
        .select("*")
        .execute()
    )

    return {
        "success": True,
        "count": len(result.data or []),
        "prices": result.data or []
    }


# ============================================================
# FUEL PRICE SLABS
# ============================================================

@app.get("/api/fuel/slabs")
def get_fuel_price_slabs(
    energy_source_id: Optional[int] = None
):
    require_database()

    query = (
        supabase
        .table("fuel_price_slabs")
        .select("*")
    )

    if energy_source_id is not None:
        query = query.eq(
            "energy_source_id",
            energy_source_id
        )

    result = query.order("energy_source_id").execute()

    return {
        "success": True,
        "count": len(result.data or []),
        "slabs": result.data or []
    }


# ============================================================
# FARE REVISIONS
# ============================================================

@app.get("/api/fare-revisions")
def get_fare_revisions(
    fare_rule_id: Optional[int] = None
):
    require_database()

    query = (
        supabase
        .table("fare_revisions")
        .select("*")
    )

    if fare_rule_id is not None:
        query = query.eq(
            "fare_rule_id",
            fare_rule_id
        )

    result = query.order(
        "id",
        desc=True
    ).execute()

    return {
        "success": True,
        "count": len(result.data or []),
        "revisions": result.data or []
    }


# ============================================================
# INSERT / UPDATE CURRENT FUEL PRICE
# ============================================================

@app.post("/api/fuel/current")
def update_current_fuel_price(
    request: FuelPriceRequest
):
    require_database()

    # Check whether a current price already exists
    existing = (
        supabase
        .table("current_fuel_prices")
        .select("*")
        .eq(
            "energy_source_id",
            request.energy_source_id
        )
        .limit(1)
        .execute()
    )

    payload = {
        "energy_source_id": request.energy_source_id,
        "price": request.price
    }

    if request.effective_from is not None:
        payload["effective_from"] = (
            request.effective_from
        )

    if request.source_id is not None:
        payload["source_id"] = request.source_id

    if request.notes is not None:
        payload["notes"] = request.notes

    if existing.data:

        row_id = existing.data[0]["id"]

        result = (
            supabase
            .table("current_fuel_prices")
            .update(payload)
            .eq("id", row_id)
            .execute()
        )

        return {
            "success": True,
            "action": "updated",
            "price": result.data
        }

    result = (
        supabase
        .table("current_fuel_prices")
        .insert(payload)
        .execute()
    )

    return {
        "success": True,
        "action": "created",
        "price": result.data
    }


# ============================================================
# DATABASE STATUS
# ============================================================

@app.get("/api/status")
def database_status():
    require_database()

    try:
        categories = (
            supabase
            .table("vehicle_categories")
            .select("id")
            .execute()
        )

        vehicles = (
            supabase
            .table("vehicles")
            .select("id")
            .execute()
        )

        fare_rules = (
            supabase
            .table("fare_rules")
            .select("id")
            .execute()
        )

        return {
            "success": True,
            "database": "connected",
            "vehicle_categories": len(
                categories.data or []
            ),
            "vehicles": len(
                vehicles.data or []
            ),
            "fare_rules": len(
                fare_rules.data or []
            )
        }

    except Exception as e:

        return {
            "success": False,
            "database": "error",
            "error": str(e)
        }


# ============================================================
# ERROR HANDLER
# ============================================================

@app.get("/api")
def api_root():
    return {
        "success": True,
        "message": "Fare Keralam API",
        "endpoints": {
            "health": "/api/health",
            "categories": "/api/categories",
            "energy_sources": "/api/energy-sources",
            "vehicles": "/api/vehicles",
            "vehicle_options": "/api/vehicle-options",
            "fare_rules": "/api/fare-rules",
            "fare_slabs": "/api/fare-slabs",
            "fare_calculate": "/api/fare/calculate",
            "fuel_current": "/api/fuel/current",
            "fuel_slabs": "/api/fuel/slabs",
            "fare_revisions": "/api/fare-revisions",
            "status": "/api/status"
        }
    }