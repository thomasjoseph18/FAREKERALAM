/* ============================================================
   FARE KERALAM - FRONTEND API ENGINE
   ============================================================
   Connects the polished frontend to:

   Render API:
   https://farekeralam.onrender.com

   Main endpoints:
   GET  /api/categories
   GET  /api/energy-sources
   GET  /api/vehicles
   GET  /api/vehicle-options
   POST /api/fare/calculate

   IMPORTANT:
   - No fake universal fare
   - No hard-coded vehicle fare
   - Fare comes from backend/database
   - Vehicle/category/fuel selection is respected
   ============================================================ */

"use strict";

/* ============================================================
   CONFIGURATION
   ============================================================ */

const API_BASE_URL = "https://farekeralam.onrender.com/api";

const API = {
    categories: `${API_BASE_URL}/categories`,
    energySources: `${API_BASE_URL}/energy-sources`,
    vehicles: `${API_BASE_URL}/vehicles`,
    vehicleOptions: `${API_BASE_URL}/vehicle-options`,
    calculate: `${API_BASE_URL}/fare/calculate`,
    health: `${API_BASE_URL}/health`
};


/* ============================================================
   APPLICATION STATE
   ============================================================ */

const state = {
    categories: [],
    energySources: [],
    vehicles: [],

    selectedCategory: null,
    selectedEnergy: null,
    selectedVehicle: null,
    selectedSeating: null,

    lastCalculation: null,

    loading: false
};


/* ============================================================
   DOM HELPERS
   ============================================================ */

function $(selector) {
    return document.querySelector(selector);
}

function $all(selector) {
    return [...document.querySelectorAll(selector)];
}

function findElement(...selectors) {
    for (const selector of selectors) {
        const element = document.querySelector(selector);

        if (element) {
            return element;
        }
    }

    return null;
}


/* ============================================================
   COMMON ELEMENT LOOKUP
   ============================================================ */

const elements = {
    category: findElement(
        "#category",
        "#vehicleCategory",
        "#vehicle-category",
        "#categorySelect",
        '[name="category"]'
    ),

    energy: findElement(
        "#energy",
        "#energySource",
        "#energy-source",
        "#fuel",
        "#fuelType",
        "#fuel-type",
        '[name="energy_source"]',
        '[name="energy"]'
    ),

    vehicle: findElement(
        "#vehicle",
        "#vehicleModel",
        "#vehicle-model",
        "#vehicleSelect",
        '[name="vehicle"]',
        '[name="vehicle_id"]'
    ),

    seating: findElement(
        "#seating",
        "#seatingCapacity",
        "#seating-capacity",
        "#capacity",
        '[name="seating_capacity"]'
    ),

    distance: findElement(
        "#distance",
        "#distanceKm",
        "#distance-km",
        "#distanceInput",
        '[name="distance_km"]'
    ),

    calculateButton: findElement(
        "#calculateFare",
        "#calculate-fare",
        "#calculateBtn",
        "#calculate",
        '[data-action="calculate"]'
    ),

    fare: findElement(
        "#fare",
        "#fareAmount",
        "#fare-amount",
        "#resultFare",
        "#totalFare",
        ".fare-amount",
        '[data-fare]'
    ),

    result: findElement(
        "#result",
        "#fareResult",
        "#fare-result",
        ".fare-result",
        ".result-card"
    ),

    resultVehicle: findElement(
        "#resultVehicle",
        "#result-vehicle",
        '[data-result="vehicle"]'
    ),

    resultCategory: findElement(
        "#resultCategory",
        "#result-category",
        '[data-result="category"]'
    ),

    resultDistance: findElement(
        "#resultDistance",
        "#result-distance",
        '[data-result="distance"]'
    ),

    resultMethod: findElement(
        "#resultMethod",
        "#result-method",
        '[data-result="method"]'
    ),

    error: findElement(
        "#error",
        "#errorMessage",
        "#error-message",
        ".error-message"
    ),

    loading: findElement(
        "#loading",
        "#loadingScreen",
        ".loading-screen"
    )
};


/* ============================================================
   INITIALIZATION
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {

    console.log("Fare Keralam frontend starting...");

    initializeApplication();

});


async function initializeApplication() {

    showLoading(true);

    try {

        await loadCategories();

        await loadEnergySources();

        await loadVehicles();

        setupEventListeners();

        setupNavigation();

        setupDistanceInput();

        setupInitialUI();

        console.log("Fare Keralam frontend ready.");

    } catch (error) {

        console.error(
            "Fare Keralam initialization failed:",
            error
        );

        showError(
            "Unable to connect to Fare Keralam server. Please try again."
        );

    } finally {

        showLoading(false);

    }
}


/* ============================================================
   API REQUEST HELPER
   ============================================================ */

async function apiRequest(url, options = {}) {

    const response = await fetch(url, {
        ...options,
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    let data = null;

    try {
        data = await response.json();
    } catch {
        data = null;
    }

    if (!response.ok) {

        let message = "Server request failed.";

        if (data?.detail) {

            if (typeof data.detail === "string") {
                message = data.detail;
            }

            else if (typeof data.detail === "object") {
                message =
                    data.detail.message ||
                    "Unable to complete the request.";
            }
        }

        throw new Error(message);
    }

    return data;
}


/* ============================================================
   LOAD CATEGORIES
   ============================================================ */

async function loadCategories() {

    const data = await apiRequest(API.categories);

    state.categories = data.categories || [];

    console.log(
        "Categories loaded:",
        state.categories
    );

    populateCategorySelect();
}


/* ============================================================
   LOAD ENERGY SOURCES
   ============================================================ */

async function loadEnergySources() {

    try {

        const data = await apiRequest(
            API.energySources
        );

        state.energySources =
            data.energy_sources || [];

        console.log(
            "Energy sources loaded:",
            state.energySources
        );

        populateEnergySelect();

    } catch (error) {

        console.warn(
            "Energy source endpoint unavailable:",
            error
        );

        /*
         * Fallback names are only used for the dropdown.
         * They are NOT used to calculate fares.
         */

        state.energySources = [
            { id: 1, name: "Petrol" },
            { id: 2, name: "Diesel" },
            { id: 3, name: "CNG" },
            { id: 4, name: "Electricity" },
            { id: 5, name: "Hybrid" }
        ];

        populateEnergySelect();
    }
}


/* ============================================================
   LOAD VEHICLES
   ============================================================ */

async function loadVehicles() {

    const data = await apiRequest(
        API.vehicles
    );

    state.vehicles =
        data.vehicles || [];

    console.log(
        `Loaded ${state.vehicles.length} vehicles.`
    );

    populateVehicleSelect();
}


/* ============================================================
   CATEGORY DROPDOWN
   ============================================================ */

function populateCategorySelect() {

    const select = elements.category;

    if (!select) {

        console.warn(
            "Category select not found."
        );

        return;
    }

    const currentValue = select.value;

    select.innerHTML = "";

    addPlaceholder(
        select,
        "Select vehicle category"
    );

    state.categories.forEach(category => {

        const option =
            document.createElement("option");

        option.value = category.name;

        option.textContent = category.name;

        option.dataset.categoryId =
            category.id;

        option.dataset.requiresModel =
            category.requires_model;

        option.dataset.requiresSeating =
            category.requires_seating_capacity;

        select.appendChild(option);
    });

    if (currentValue) {
        select.value = currentValue;
    }

}


/* ============================================================
   ENERGY DROPDOWN
   ============================================================ */

function populateEnergySelect() {

    const select = elements.energy;

    if (!select) {

        console.warn(
            "Energy select not found."
        );

        return;
    }

    const currentValue = select.value;

    select.innerHTML = "";

    addPlaceholder(
        select,
        "Select fuel / energy"
    );

    state.energySources.forEach(energy => {

        const option =
            document.createElement("option");

        option.value = energy.name;

        option.textContent = energy.name;

        option.dataset.energyId =
            energy.id;

        select.appendChild(option);
    });

    if (currentValue) {
        select.value = currentValue;
    }

}


/* ============================================================
   VEHICLE DROPDOWN
   ============================================================ */

function populateVehicleSelect() {

    const select = elements.vehicle;

    if (!select) {

        console.warn(
            "Vehicle select not found."
        );

        return;
    }

    const filtered =
        getFilteredVehicles();

    select.innerHTML = "";

    addPlaceholder(
        select,
        filtered.length
            ? "Select vehicle"
            : "No matching vehicles"
    );

    filtered.forEach(vehicle => {

        const option =
            document.createElement("option");

        option.value = vehicle.id;

        option.textContent =
            buildVehicleLabel(vehicle);

        option.dataset.vehicleId =
            vehicle.id;

        option.dataset.categoryId =
            vehicle.category_id;

        option.dataset.energyId =
            vehicle.energy_source_id;

        if (vehicle.seating_capacity !== null) {

            option.dataset.seating =
                vehicle.seating_capacity;
        }

        select.appendChild(option);
    });

}


/* ============================================================
   FILTER VEHICLES
   ============================================================ */

function getFilteredVehicles() {

    let vehicles =
        [...state.vehicles];

    const category =
        getSelectedCategoryObject();

    const energy =
        getSelectedEnergyObject();

    const seating =
        getSelectedSeating();

    if (category) {

        vehicles =
            vehicles.filter(vehicle =>
                Number(vehicle.category_id) ===
                Number(category.id)
            );
    }

    if (energy) {

        vehicles =
            vehicles.filter(vehicle =>
                Number(vehicle.energy_source_id) ===
                Number(energy.id)
            );
    }

    if (seating !== null) {

        vehicles =
            vehicles.filter(vehicle => {

                if (
                    vehicle.seating_capacity ===
                    null
                ) {
                    return true;
                }

                return Number(
                    vehicle.seating_capacity
                ) === Number(seating);

            });
    }

    return vehicles;
}


/* ============================================================
   VEHICLE LABEL
   ============================================================ */

function buildVehicleLabel(vehicle) {

    let label =
        vehicle.name || "Vehicle";

    if (
        vehicle.seating_capacity !== null &&
        vehicle.seating_capacity !== undefined
    ) {

        label +=
            ` — ${vehicle.seating_capacity} seats`;
    }

    return label;
}


/* ============================================================
   PLACEHOLDER
   ============================================================ */

function addPlaceholder(select, text) {

    const option =
        document.createElement("option");

    option.value = "";

    option.textContent = text;

    option.disabled = true;

    option.selected = true;

    select.appendChild(option);
}


/* ============================================================
   EVENT LISTENERS
   ============================================================ */

function setupEventListeners() {

    if (elements.category) {

        elements.category.addEventListener(
            "change",
            handleCategoryChange
        );
    }

    if (elements.energy) {

        elements.energy.addEventListener(
            "change",
            handleEnergyChange
        );
    }

    if (elements.seating) {

        elements.seating.addEventListener(
            "change",
            handleSeatingChange
        );
    }

    if (elements.vehicle) {

        elements.vehicle.addEventListener(
            "change",
            handleVehicleChange
        );
    }

    if (elements.calculateButton) {

        elements.calculateButton.addEventListener(
            "click",
            calculateFare
        );
    }

    /*
     * Also support forms.
     */

    $all("form").forEach(form => {

        form.addEventListener(
            "submit",
            event => {

                if (
                    form.querySelector(
                        "#distance, #distanceKm, #distance-km"
                    )
                ) {

                    event.preventDefault();

                    calculateFare();
                }

            }
        );
    });

}


/* ============================================================
   CATEGORY CHANGE
   ============================================================ */

function handleCategoryChange() {

    state.selectedCategory =
        elements.category?.value || null;

    state.selectedVehicle = null;

    updateCategoryRequirements();

    populateVehicleSelect();

    updateSeatingOptions();

    clearFareResult();

    console.log(
        "Category:",
        state.selectedCategory
    );
}


/* ============================================================
   ENERGY CHANGE
   ============================================================ */

function handleEnergyChange() {

    state.selectedEnergy =
        elements.energy?.value || null;

    state.selectedVehicle = null;

    populateVehicleSelect();

    clearFareResult();

    console.log(
        "Energy:",
        state.selectedEnergy
    );
}


/* ============================================================
   SEATING CHANGE
   ============================================================ */

function handleSeatingChange() {

    state.selectedSeating =
        getSelectedSeating();

    state.selectedVehicle = null;

    populateVehicleSelect();

    clearFareResult();
}


/* ============================================================
   VEHICLE CHANGE
   ============================================================ */

function handleVehicleChange() {

    const vehicleId =
        Number(elements.vehicle?.value);

    if (!vehicleId) {

        state.selectedVehicle = null;

        return;
    }

    state.selectedVehicle =
        state.vehicles.find(
            vehicle =>
                Number(vehicle.id) ===
                vehicleId
        ) || null;

    console.log(
        "Selected vehicle:",
        state.selectedVehicle
    );

    clearFareResult();
}


/* ============================================================
   CATEGORY REQUIREMENTS
   ============================================================ */

function updateCategoryRequirements() {

    const category =
        getSelectedCategoryObject();

    if (!category) {
        return;
    }

    const requiresSeating =
        Boolean(
            category.requires_seating_capacity
        );

    if (elements.seating) {

        const wrapper =
            elements.seating.closest(
                ".form-group, .field, .input-group"
            );

        if (wrapper) {

            wrapper.style.display =
                requiresSeating
                    ? ""
                    : "none";
        }

        elements.seating.required =
            requiresSeating;
    }

}


/* ============================================================
   SEATING OPTIONS
   ============================================================ */

function updateSeatingOptions() {

    const select =
        elements.seating;

    if (!select) {
        return;
    }

    const category =
        getSelectedCategoryObject();

    const requiresSeating =
        category &&
        category.requires_seating_capacity;

    if (!requiresSeating) {

        select.value = "";

        state.selectedSeating = null;

        return;
    }

    const categoryVehicles =
        state.vehicles.filter(
            vehicle =>
                Number(vehicle.category_id) ===
                Number(category.id)
        );

    const capacities =
        [
            ...new Set(
                categoryVehicles
                    .map(
                        vehicle =>
                            vehicle.seating_capacity
                    )
                    .filter(
                        capacity =>
                            capacity !== null &&
                            capacity !== undefined
                    )
            )
        ]
        .sort(
            (a, b) => Number(a) - Number(b)
        );

    const current =
        select.value;

    select.innerHTML = "";

    addPlaceholder(
        select,
        "Select seating capacity"
    );

    capacities.forEach(capacity => {

        const option =
            document.createElement("option");

        option.value = capacity;

        option.textContent =
            `${capacity} seats`;

        select.appendChild(option);
    });

    if (
        current &&
        capacities.includes(Number(current))
    ) {

        select.value = current;
    }

}


/* ============================================================
   GET SELECTED CATEGORY
   ============================================================ */

function getSelectedCategoryObject() {

    if (!elements.category?.value) {
        return null;
    }

    return state.categories.find(
        category =>
            category.name ===
            elements.category.value
    ) || null;
}


/* ============================================================
   GET SELECTED ENERGY
   ============================================================ */

function getSelectedEnergyObject() {

    if (!elements.energy?.value) {
        return null;
    }

    return state.energySources.find(
        energy =>
            energy.name ===
            elements.energy.value
    ) || null;
}


/* ============================================================
   GET SEATING
   ============================================================ */

function getSelectedSeating() {

    if (!elements.seating?.value) {
        return null;
    }

    const value =
        Number(elements.seating.value);

    return Number.isFinite(value)
        ? value
        : null;
}


/* ============================================================
   GET DISTANCE
   ============================================================ */

function getDistance() {

    if (!elements.distance) {
        return null;
    }

    const value =
        Number(
            String(
                elements.distance.value
            ).replace(",", ".")
        );

    if (
        !Number.isFinite(value) ||
        value <= 0
    ) {

        return null;
    }

    return value;
}


/* ============================================================
   FARE CALCULATION
   ============================================================ */

async function calculateFare() {

    if (state.loading) {
        return;
    }

    clearError();

    const category =
        getSelectedCategoryObject();

    const energy =
        getSelectedEnergyObject();

    const distance =
        getDistance();

    const seating =
        getSelectedSeating();

    /*
     * --------------------------------------------------------
     * VALIDATION
     * --------------------------------------------------------
     */

    if (!category) {

        showError(
            "Please select a vehicle category."
        );

        focusElement(elements.category);

        return;
    }

    if (!energy) {

        showError(
            "Please select a fuel or energy source."
        );

        focusElement(elements.energy);

        return;
    }

    if (!distance) {

        showError(
            "Please enter a valid journey distance."
        );

        focusElement(elements.distance);

        return;
    }

    if (
        category.requires_seating_capacity &&
        !seating
    ) {

        showError(
            "Please select the seating capacity."
        );

        focusElement(elements.seating);

        return;
    }

    /*
     * --------------------------------------------------------
     * VEHICLE
     * --------------------------------------------------------
     */

    const filteredVehicles =
        getFilteredVehicles();

    let vehicle =
        state.selectedVehicle;

    /*
     * If the user did not explicitly choose a
     * vehicle, use the first exact database
     * match for the selected combination.
     */

    if (!vehicle && filteredVehicles.length) {

        /*
         * For categories requiring a model,
         * selecting a specific vehicle is preferred.
         */

        if (category.requires_model) {

            vehicle =
                filteredVehicles[0];
        }
    }

    /*
     * --------------------------------------------------------
     * BUILD REQUEST
     * --------------------------------------------------------
     */

    const requestBody = {

        category: category.name,

        energy_source: energy.name,

        distance_km: distance,

        seating_capacity:
            seating,

        vehicle_id:
            vehicle
                ? Number(vehicle.id)
                : undefined
    };

    /*
     * Remove undefined vehicle_id.
     */

    Object.keys(requestBody).forEach(key => {

        if (
            requestBody[key] ===
            undefined
        ) {

            delete requestBody[key];
        }

    });


    console.log(
        "Fare calculation request:",
        requestBody
    );


    /*
     * --------------------------------------------------------
     * UI LOADING
     * --------------------------------------------------------
     */

    setCalculationLoading(true);


    try {

        const data =
            await apiRequest(
                API.calculate,
                {
                    method: "POST",

                    body:
                        JSON.stringify(
                            requestBody
                        )
                }
            );


        console.log(
            "Fare calculation response:",
            data
        );


        /*
         * ----------------------------------------------------
         * VERIFY SERVER RESPONSE
         * ----------------------------------------------------
         */

        if (
            !data ||
            data.success !== true ||
            !data.calculation
        ) {

            throw new Error(
                "The server returned an invalid fare response."
            );
        }


        const calculation =
            data.calculation;


        /*
         * CRITICAL:
         *
         * We NEVER create a fare ourselves here.
         *
         * The fare must come from the backend.
         */

        if (
            calculation.fare ===
            null ||
            calculation.fare ===
            undefined
        ) {

            showUnavailableFare(
                calculation
            );

            return;
        }


        const fare =
            Number(calculation.fare);


        if (
            !Number.isFinite(fare)
        ) {

            throw new Error(
                "The server returned an invalid fare."
            );
        }


        /*
         * ----------------------------------------------------
         * SAVE RESULT
         * ----------------------------------------------------
         */

        state.lastCalculation =
            calculation;


        /*
         * ----------------------------------------------------
         * DISPLAY RESULT
         * ----------------------------------------------------
         */

        displayFareResult(
            calculation
        );


    } catch (error) {

        console.error(
            "Fare calculation error:",
            error
        );

        showError(
            error.message ||
            "Unable to calculate fare."
        );

    } finally {

        setCalculationLoading(false);

    }
}


/* ============================================================
   DISPLAY FARE RESULT
   ============================================================ */

function displayFareResult(calculation) {

    const fare =
        Number(calculation.fare);

    const formattedFare =
        formatCurrency(fare);


    /*
     * Main fare
     */

    if (elements.fare) {

        elements.fare.textContent =
            formattedFare;
    }


    /*
     * Category
     */

    if (elements.resultCategory) {

        elements.resultCategory.textContent =
            calculation.category ||
            "—";
    }


    /*
     * Vehicle
     */

    if (elements.resultVehicle) {

        elements.resultVehicle.textContent =
            calculation.vehicle?.name ||
            state.selectedVehicle?.name ||
            calculation.category ||
            "—";
    }


    /*
     * Distance
     */

    if (elements.resultDistance) {

        elements.resultDistance.textContent =
            `${formatNumber(
                calculation.distance_km
            )} km`;
    }


    /*
     * Calculation method
     */

    if (elements.resultMethod) {

        elements.resultMethod.textContent =
            getCalculationMethodLabel(
                calculation.calculation_method
            );
    }


    /*
     * Show result container
     */

    if (elements.result) {

        elements.result.classList.add(
            "active",
            "show",
            "visible"
        );

        elements.result.hidden =
            false;
    }


    /*
     * Update any generic fare fields
     */

    $all(
        "[data-fare]"
    ).forEach(element => {

        element.textContent =
            formattedFare;
    });


    /*
     * Update currency fields
     */

    $all(
        "[data-currency]"
    ).forEach(element => {

        element.textContent =
            formattedFare;
    });


    /*
     * Scroll result into view on mobile
     */

    if (
        window.innerWidth < 768 &&
        elements.result
    ) {

        setTimeout(() => {

            elements.result.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

        }, 100);
    }

}


/* ============================================================
   UNAVAILABLE FARE
   ============================================================ */

function showUnavailableFare(calculation) {

    if (elements.fare) {

        elements.fare.textContent =
            "Fare unavailable";
    }

    if (elements.resultMethod) {

        elements.resultMethod.textContent =
            "No fare rule configured";
    }

    if (elements.result) {

        elements.result.classList.add(
            "active",
            "show",
            "visible"
        );

        elements.result.hidden =
            false;
    }

    showError(
        `A fare rule has not yet been configured for ${
            calculation.category || "this vehicle"
        }.`
    );
}


/* ============================================================
   CALCULATION METHOD LABEL
   ============================================================ */

function getCalculationMethodLabel(method) {

    const labels = {

        database_fare_rule:
            "Government/database fare rule",

        database_fare_slab:
            "Database fare slab",

        fuel_adjusted:
            "Fuel-adjusted fare",

        government_rule:
            "Government fare rule",

        fallback_default:
            "Default fare",

        unavailable:
            "Fare unavailable"
    };

    return (
        labels[method] ||
        method ||
        "Database fare"
    );
}


/* ============================================================
   CURRENCY
   ============================================================ */

function formatCurrency(value) {

    return new Intl.NumberFormat(
        "en-IN",
        {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: 2,
            minimumFractionDigits: 2
        }
    ).format(value);
}


/* ============================================================
   NUMBER FORMAT
   ============================================================ */

function formatNumber(value) {

    const number =
        Number(value);

    if (!Number.isFinite(number)) {
        return "0";
    }

    return number.toLocaleString(
        "en-IN",
        {
            maximumFractionDigits: 2
        }
    );
}


/* ============================================================
   DISTANCE INPUT
   ============================================================ */

function setupDistanceInput() {

    if (!elements.distance) {
        return;
    }

    elements.distance.addEventListener(
        "input",
        () => {

            /*
             * Allow only numbers and decimal point.
             */

            let value =
                elements.distance.value;

            value =
                value.replace(
                    /[^0-9.]/g,
                    ""
                );

            /*
             * Only one decimal point.
             */

            const parts =
                value.split(".");

            if (parts.length > 2) {

                value =
                    parts[0] +
                    "." +
                    parts.slice(1).join("");
            }

            elements.distance.value =
                value;

            clearFareResult();
        }
    );


    elements.distance.addEventListener(
        "keydown",
        event => {

            if (
                event.key ===
                "Enter"
            ) {

                event.preventDefault();

                calculateFare();
            }

        }
    );
}


/* ============================================================
   INITIAL UI
   ============================================================ */

function setupInitialUI() {

    clearFareResult();

    clearError();

    /*
     * Hide seating if not required.
     */

    updateCategoryRequirements();

    /*
     * Build seating choices.
     */

    updateSeatingOptions();
}


/* ============================================================
   CLEAR RESULT
   ============================================================ */

function clearFareResult() {

    if (elements.fare) {

        /*
         * Don't show a fake fare.
         */

        elements.fare.textContent =
            "₹ —";
    }

    if (elements.resultMethod) {

        elements.resultMethod.textContent =
            "Enter journey details";
    }

    if (elements.result) {

        /*
         * Don't forcibly hide the result if
         * your CSS uses it as a permanent card.
         *
         * Just remove previous state classes.
         */

        elements.result.classList.remove(
            "active",
            "show",
            "visible"
        );
    }

    state.lastCalculation =
        null;
}


/* ============================================================
   ERROR DISPLAY
   ============================================================ */

function showError(message) {

    console.error(
        "Fare Keralam:",
        message
    );

    if (elements.error) {

        elements.error.textContent =
            message;

        elements.error.classList.add(
            "active",
            "show",
            "visible"
        );

        elements.error.hidden =
            false;

        return;
    }

    /*
     * If the existing HTML doesn't have
     * an error element, create one.
     */

    createTemporaryMessage(
        message,
        "error"
    );
}


/* ============================================================
   CLEAR ERROR
   ============================================================ */

function clearError() {

    if (!elements.error) {
        return;
    }

    elements.error.textContent = "";

    elements.error.classList.remove(
        "active",
        "show",
        "visible"
    );
}


/* ============================================================
   TEMPORARY MESSAGE
   ============================================================ */

function createTemporaryMessage(
    message,
    type = "error"
) {

    const existing =
        document.querySelector(
            ".fare-k-temp-message"
        );

    if (existing) {
        existing.remove();
    }

    const element =
        document.createElement("div");

    element.className =
        `fare-k-temp-message ${type}`;

    element.textContent =
        message;

    element.style.cssText = `
        position: fixed;
        left: 50%;
        bottom: 25px;
        transform: translateX(-50%);
        z-index: 99999;
        max-width: 90%;
        padding: 14px 20px;
        border-radius: 12px;
        background: rgba(20, 20, 30, 0.95);
        color: white;
        border: 1px solid rgba(255,255,255,.15);
        box-shadow: 0 15px 40px rgba(0,0,0,.25);
        font-size: 14px;
        text-align: center;
        backdrop-filter: blur(15px);
    `;

    document.body.appendChild(
        element
    );

    setTimeout(() => {

        element.remove();

    }, 4500);
}


/* ============================================================
   LOADING STATE
   ============================================================ */

function showLoading(show) {

    if (!elements.loading) {
        return;
    }

    if (show) {

        elements.loading.classList.add(
            "active",
            "show",
            "visible"
        );

    } else {

        elements.loading.classList.remove(
            "active",
            "show",
            "visible"
        );

    }
}


/* ============================================================
   CALCULATION BUTTON LOADING
   ============================================================ */

function setCalculationLoading(
    loading
) {

    state.loading =
        loading;

    const button =
        elements.calculateButton;

    if (!button) {
        return;
    }

    if (loading) {

        button.dataset.originalText =
            button.textContent;

        button.disabled =
            true;

        button.setAttribute(
            "aria-busy",
            "true"
        );

        button.textContent =
            "Calculating…";

        button.classList.add(
            "loading"
        );

    } else {

        button.disabled =
            false;

        button.removeAttribute(
            "aria-busy"
        );

        button.textContent =
            button.dataset.originalText ||
            "Calculate Fare";

        button.classList.remove(
            "loading"
        );
    }
}


/* ============================================================
   FOCUS HELPER
   ============================================================ */

function focusElement(element) {

    if (!element) {
        return;
    }

    try {

        element.focus();

    } catch {
        // Ignore focus errors.
    }
}


/* ============================================================
   NAVIGATION
   ============================================================ */

function setupNavigation() {

    /*
     * Mobile menu
     */

    const menuButton =
        findElement(
            "#menuToggle",
            "#menu-toggle",
            ".menu-toggle",
            "[data-menu-toggle]"
        );

    const nav =
        findElement(
            "#nav",
            "#navbar",
            ".navbar",
            ".nav-menu",
            "[data-navigation]"
        );

    if (
        menuButton &&
        nav
    ) {

        menuButton.addEventListener(
            "click",
            () => {

                nav.classList.toggle(
                    "active"
                );

                menuButton.classList.toggle(
                    "active"
                );
            }
        );
    }


    /*
     * Smooth anchor navigation
     */

    $all(
        'a[href^="#"]'
    ).forEach(link => {

        link.addEventListener(
            "click",
            event => {

                const targetId =
                    link.getAttribute(
                        "href"
                    );

                if (
                    !targetId ||
                    targetId === "#"
                ) {
                    return;
                }

                const target =
                    document.querySelector(
                        targetId
                    );

                if (!target) {
                    return;
                }

                event.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

                if (nav) {
                    nav.classList.remove(
                        "active"
                    );
                }

                if (menuButton) {
                    menuButton.classList.remove(
                        "active"
                    );
                }

            }
        );
    });
}


/* ============================================================
   BACKEND HEALTH CHECK
   ============================================================ */

async function checkBackendHealth() {

    try {

        const data =
            await apiRequest(
                API.health
            );

        console.log(
            "Fare Keralam backend:",
            data
        );

        return data;

    } catch (error) {

        console.error(
            "Backend health check failed:",
            error
        );

        return null;
    }
}


/* ============================================================
   OPTIONAL GLOBAL API
   ============================================================
   Useful if other frontend components need access.
   ============================================================ */

window.FareKeralam = {

    calculateFare,

    loadCategories,

    loadVehicles,

    loadEnergySources,

    checkBackendHealth,

    getState: () => ({
        ...state
    }),

    API
};


/* ============================================================
   DEBUG
   ============================================================ */

console.log(
    "%cFARE KERALAM",
    "font-size:20px;font-weight:800;"
);

console.log(
    "API:",
    API_BASE_URL
);