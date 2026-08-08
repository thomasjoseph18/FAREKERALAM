# ============================================================
# FARE KERALAM - MAIN API
# ============================================================

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client, Client


# ============================================================
# CONFIGURATION
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Fare Keralam API",
    description="Kerala government fare and fuel-price revision API",
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
# HELPERS
# ============================================================

def require_database():
    if supabase is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured"
        )


def db_error(error):
    return str(error) if error else "Unknown database error"


# ============================================================
# HEALTH
# ============================================================

@app.get("/")
def root():
    return {
        "name": "Fare Keralam API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
def health():
    database_configured = supabase is not None

    return {
        "status": "healthy",
        "database_configured": database_configured
    }


# ============================================================
# VEHICLES
# ============================================================

@app.get("/api/vehicles")
def get_vehicles(
    category_id: Optional[int] = Query(default=None),
    energy_source_id: Optional[int] = Query(default=None)
):
    require_database()

    try:
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

        result = query.execute()

        vehicles = result.data or []

        return {
            "success": True,
            "count": len(vehicles),
            "vehicles": vehicles
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=db_error(e)
        )


# ============================================================
# VEHICLE OPTIONS
#
# Returns:
# Category
#   -> Fuel
#       -> Seating capacities
#
# Uses the government classification currently stored
# in vehicle_categories.
# ============================================================

@app.get("/api/vehicle-options")
def get_vehicle_options():
    require_database()

    try:
        categories_result = (
            supabase
            .table("vehicle_categories")
            .select("id,name")
            .order("id")
            .execute()
        )

        categories = categories_result.data or []

        vehicles_result = (
            supabase
            .table("vehicles")
            .select(
                "id,category_id,energy_source_id,"
                "name,seating_capacity,active"
            )
            .eq("active", True)
            .execute()
        )

        vehicles = vehicles_result.data or []

        energy_result = (
            supabase
            .table("energy_sources")
            .select("id,name")
            .order("id")
            .execute()
        )

        energy_sources = energy_result.data or []

        energy_map = {
            item["id"]: item["name"]
            for item in energy_sources
        }

        output = {}

        for category in categories:
            category_name = category["name"]

            output[category_name] = {}

            category_vehicles = [
                v for v in vehicles
                if v["category_id"] == category["id"]
            ]

            for vehicle in category_vehicles:
                fuel = energy_map.get(
                    vehicle["energy_source_id"],
                    "Unknown"
                )

                if fuel not in output[category_name]:
                    output[category_name][fuel] = []

                seating = vehicle.get("seating_capacity")

                if seating is not None:
                    if seating not in output[category_name][fuel]:
                        output[category_name][fuel].append(seating)

            for fuel in output[category_name]:
                output[category_name][fuel].sort()

        return {
            "success": True,
            "categories": output
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=db_error(e)
        )


# ============================================================
# FUEL PRICE MODEL
# ============================================================

class FuelPriceRequest(BaseModel):
    energy_source_id: int
    price: float = Field(gt=0)
    unit: str = "litre"
    location: Optional[str] = None
    source_id: Optional[int] = None
    observed_at: Optional[datetime] = None


# ============================================================
# ADD CURRENT FUEL PRICE
#
# This records a new price.
#
# It DOES NOT change government fares.
# ============================================================

@app.post("/api/fuel-prices")
def add_fuel_price(request: FuelPriceRequest):
    require_database()

    try:
        # Mark previous current prices for this fuel as not current.
        (
            supabase
            .table("current_fuel_prices")
            .update({"is_current": False})
            .eq(
                "energy_source_id",
                request.energy_source_id
            )
            .eq("is_current", True)
            .execute()
        )

        observed_at = (
            request.observed_at
            if request.observed_at
            else datetime.now(timezone.utc)
        )

        payload = {
            "energy_source_id": request.energy_source_id,
            "price": request.price,
            "unit": request.unit,
            "location": request.location,
            "source_id": request.source_id,
            "observed_at": observed_at.isoformat(),
            "is_current": True
        }

        result = (
            supabase
            .table("current_fuel_prices")
            .insert(payload)
            .execute()
        )

        return {
            "success": True,
            "message": "Fuel price recorded successfully",
            "fuel_price": result.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=db_error(e)
        )


# ============================================================
# CURRENT FUEL PRICES
# ============================================================

@app.get("/api/fuel-prices")
def get_current_fuel_prices():
    require_database()

    try:
        result = (
            supabase
            .table("current_fuel_prices")
            .select("*")
            .eq("is_current", True)
            .order("energy_source_id")
            .execute()
        )

        return {
            "success": True,
            "count": len(result.data or []),
            "prices": result.data or []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=db_error(e)
        )


# ============================================================
# FUEL PRICE SLABS
# ============================================================

@app.get("/api/fuel-price-slabs")
def get_fuel_price_slabs(
    energy_source_id: Optional[int] = Query(default=None)
):
    require_database()

    try:
        query = (
            supabase
            .table("fuel_price_slabs")
            .select("*")
            .order("energy_source_id")
            .order("min_price")
        )

        if energy_source_id is not None:
            query = query.eq(
                "energy_source_id",
                energy_source_id
            )

        result = query.execute()

        return {
            "success": True,
            "count": len(result.data or []),
            "slabs": result.data or []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=db_error(e)
        )


# ============================================================
# FIND APPLICABLE FUEL SLAB
#
# This endpoint answers:
#
# "At the current fuel price, which configured
#  fuel-price slab applies?"
#
# It does NOT modify fares.
# ============================================================

@app.get("/api/fuel-price-status")
def get_fuel_price_status(
    energy_source_id: Optional[int] = Query(default=None)
):
    require_database()

    try:
        query = (
            supabase
            .table("current_fuel_slab_status")
            .select("*")
        )

        if energy_source_id is not None:
            query = query.eq(
                "energy_source_id",
                energy_source_id
            )

        result = query.execute()

        return {
            "success": True,
            "count": len(result.data or []),
            "fuel_prices": result.data or []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=db_error(e)
        )


# ============================================================
# FARE RULES
# ============================================================

@app.get("/api/fare-rules")
def get_fare_rules(
    category_id: Optional[int] = Query(default=None)
):
    require_database()

    try:
        query = (
            supabase
            .table("fare_rules")
            .select("*")
            .eq("status", "active")
            .order("id")
        )

        if category_id is not None:
            query = query.eq(
                "category_id",
                category_id
            )

        result = query.execute()

        return {
            "success": True,
            "count": len(result.data or []),
            "fare_rules": result.data or []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=db_error(e)
        )


# ============================================================
# FARE SLABS
# ============================================================

@app.get("/api/fare-slabs/{fare_rule_id}")
def get_fare_slabs(fare_rule_id: int):
    require_database()

    try:
        result = (
            supabase
            .table("fare_slabs")
            .select("*")
            .eq("fare_rule_id", fare_rule_id)
            .order("from_km")
            .execute()
        )

        return {
            "success": True,
            "fare_rule_id": fare_rule_id,
            "count": len(result.data or []),
            "slabs": result.data or []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=db_error(e)
        )


# ============================================================
# FARE REVISIONS
# ============================================================

@app.get("/api/fare-revisions")
def get_fare_revisions(
    fare_rule_id: Optional[int] = Query(default=None)
):
    require_database()

    try:
        query = (
            supabase
            .table("fare_revisions")
            .select("*")
            .order("created_at", desc=True)
        )

        if fare_rule_id is not None:
            query = query.eq(
                "fare_rule_id",
                fare_rule_id
            )

        result = query.execute()

        return {
            "success": True,
            "count": len(result.data or []),
            "revisions": result.data or []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=db_error(e)
        )


# ============================================================
# FARE CALCULATION
#
# Uses the existing government fare rule + fare slabs.
#
# Fuel-price revision is deliberately NOT applied yet.
# ============================================================

@app.get("/api/calculate-fare")
def calculate_fare(
    fare_rule_id: int,
    distance_km: float = Query(gt=0)
):
    require_database()

    try:
        rule_result = (
            supabase
            .table("fare_rules")
            .select("*")
            .eq("id", fare_rule_id)
            .single()
            .execute()
        )

        rule = rule_result.data

        if not rule:
            raise HTTPException(
                status_code=404,
                detail="Fare rule not found"
            )

        slab_result = (
            supabase
            .table("fare_slabs")
            .select("*")
            .eq("fare_rule_id", fare_rule_id)
            .order("from_km")
            .execute()
        )

        slabs = slab_result.data or []

        minimum_distance = float(
            rule["minimum_distance_km"]
        )

        minimum_fare = float(
            rule["minimum_fare"]
        )

        if distance_km <= minimum_distance:
            return {
                "success": True,
                "fare_rule_id": fare_rule_id,
                "distance_km": distance_km,
                "minimum_fare": minimum_fare,
                "calculated_fare": minimum_fare,
                "fuel_revision_applied": False
            }

        fare = minimum_fare
        remaining_distance = distance_km - minimum_distance

        for slab in slabs:
            from_km = float(slab["from_km"])
            to_km = slab["to_km"]
            rate = float(slab["rate_per_km"])

            if to_km is None:
                applicable_distance = remaining_distance

            else:
                slab_width = float(to_km) - from_km
                applicable_distance = min(
                    remaining_distance,
                    slab_width
                )

            if applicable_distance > 0:
                fare += applicable_distance * rate
                remaining_distance -= applicable_distance

            if remaining_distance <= 0:
                break

        return {
            "success": True,
            "fare_rule_id": fare_rule_id,
            "distance_km": distance_km,
            "government_base_fare": round(fare, 2),
            "calculated_fare": round(fare, 2),
            "fuel_revision_applied": False,
            "message": (
                "Government base fare calculated. "
                "Fuel-price revision is not active yet."
            )
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=db_error(e)
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )