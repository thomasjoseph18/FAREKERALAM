/* ============================================================
   FARE KERALAM - UPDATED FRONTEND SCRIPT
   ============================================================
   Backend:
   https://farekeralam.onrender.com

   API:
   GET  /api/categories
   GET  /api/energy-sources
   GET  /api/vehicles
   GET  /api/vehicle-options
   GET  /api/health
   POST /api/fare/calculate

   IMPORTANT:
   - No hard-coded fare calculation
   - Fare always comes from the backend/database
   - Frontend only collects user input and displays API results
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


/* ============================================================
   DOM ELEMENTS
============================================================ */

const elements = {
    pageLoader: $("#pageLoader"),

    header: $("#siteHeader"),

    mobileMenuBtn: $("#mobileMenuBtn"),
    mainNav: $("#mainNav"),

    fareForm: $("#fareForm"),

    category: $("#category"),
    energy: $("#energy"),
    vehicle: $("#vehicle"),
    seating: $("#seating"),
    distance: $("#distance"),

    vehicleGroup: $("#vehicleGroup"),
    seatingGroup: $("#seatingGroup"),

    calculateBtn: $("#calculateBtn"),

    resultCard: $("#resultCard"),
    resultEmpty: $("#resultEmpty"),
    resultSuccess: $("#resultSuccess"),
    resultError: $("#resultError"),

    fareAmount: $("#fareAmount"),

    resultCategory: $("#resultCategory"),
    resultEnergy: $("#resultEnergy"),
    resultDistance: $("#resultDistance"),
    resultSeats: $("#resultSeats"),

    calculationMethod: $("#calculationMethod"),
    fareRuleNote: $("#fareRuleNote"),

    resetBtn: $("#resetBtn"),
    retryBtn: $("#retryBtn"),

    errorMessage: $("#errorMessage"),

    footerStatus: $("#footerStatus"),
    currentYear: $("#currentYear"),

    categoryCount: $("#categoryCount"),
    energyCount: $("#energyCount"),
    vehicleCount: $("#vehicleCount"),
    vehicleCountStat: $("#vehicleCountStat"),

    toast: $("#toast"),
    toastMessage: $("#toastMessage")
};


/* ============================================================
   INITIALIZATION
============================================================ */

document.addEventListener("DOMContentLoaded", () => {

    initializeApplication();

});


async function initializeApplication() {

    setCurrentYear();

    setupNavigation();

    setupEventListeners();

    setupDistanceInput();

    showResultEmpty();

    try {

        showPageLoader(true);

        await checkAPIHealth();

        await loadCategories();

        await loadEnergySources();

        await loadVehicles();

        updateStatistics();

        setupInitialUI();

        setFooterStatus(
            "API connected",
            true
        );

        console.log(
            "Fare Keralam frontend initialized successfully."
        );

    } catch (error) {

        console.error(
            "Fare Keralam initialization error:",
            error
        );

        setFooterStatus(
            "API unavailable",
            false
        );

        showToast(
            "Unable to load Fare Keralam data."
        );

    } finally {

        setTimeout(() => {
            showPageLoader(false);
        }, 500);

    }

}


/* ============================================================
   API REQUEST HELPER
============================================================ */

async function apiRequest(url, options = {}) {

    const requestOptions = {
        ...options,
        headers: {
            "Accept": "application/json",
            ...(options.body
                ? {
                    "Content-Type":
                        "application/json"
                }
                : {}),
            ...(options.headers || {})
        }
    };

    const response =
        await fetch(
            url,
            requestOptions
        );

    let data = null;

    try {

        data =
            await response.json();

    } catch {

        data = null;

    }

    if (!response.ok) {

        let message =
            "Server request failed.";

        if (data?.detail) {

            if (
                typeof data.detail ===
                "string"
            ) {

                message =
                    data.detail;

            } else if (
                typeof data.detail ===
                "object"
            ) {

                message =
                    data.detail.message ||
                    data.detail.detail ||
                    message;

            }

        }

        throw new Error(message);

    }

    return data;

}


/* ============================================================
   API HEALTH
============================================================ */

async function checkAPIHealth() {

    try {

        const data =
            await apiRequest(
                API.health
            );

        console.log(
            "API health:",
            data
        );

        if (
            data &&
            data.status === "healthy"
        ) {

            setFooterStatus(
                "API online",
                true
            );

        }

        return data;

    } catch (error) {

        console.warn(
            "Health check failed:",
            error
        );

        throw error;

    }

}


/* ============================================================
   LOAD CATEGORIES
============================================================ */

async function loadCategories() {

    const data =
        await apiRequest(
            API.categories
        );

    state.categories =
        Array.isArray(
            data.categories
        )
            ? data.categories
            : [];

    console.log(
        "Categories:",
        state.categories
    );

    populateCategorySelect();

}


/* ============================================================
   LOAD ENERGY SOURCES
============================================================ */

async function loadEnergySources() {

    const data =
        await apiRequest(
            API.energySources
        );

    state.energySources =
        Array.isArray(
            data.energy_sources
        )
            ? data.energy_sources
            : [];

    console.log(
        "Energy sources:",
        state.energySources
    );

    populateEnergySelect();

}


/* ============================================================
   LOAD VEHICLES
============================================================ */

async function loadVehicles() {

    const data =
        await apiRequest(
            API.vehicles
        );

    state.vehicles =
        Array.isArray(
            data.vehicles
        )
            ? data.vehicles
            : [];

    console.log(
        "Vehicles:",
        state.vehicles
    );

    populateVehicleSelect();

}


/* ============================================================
   CATEGORY DROPDOWN
============================================================ */

function populateCategorySelect() {

    const select =
        elements.category;

    if (!select) {
        return;
    }

    select.innerHTML = "";

    addPlaceholder(
        select,
        "Select vehicle category"
    );

    state.categories.forEach(
        category => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                category.name;

            option.textContent =
                category.name;

            option.dataset.id =
                category.id;

            option.dataset.requiresModel =
                category.requires_model;

            option.dataset.requiresSeating =
                category.requires_seating_capacity;

            select.appendChild(
                option
            );

        }
    );

}


/* ============================================================
   ENERGY DROPDOWN
============================================================ */

function populateEnergySelect() {

    const select =
        elements.energy;

    if (!select) {
        return;
    }

    select.innerHTML = "";

    addPlaceholder(
        select,
        "Select fuel / energy"
    );

    state.energySources.forEach(
        energy => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                energy.name;

            option.textContent =
                energy.name;

            option.dataset.id =
                energy.id;

            select.appendChild(
                option
            );

        }
    );

}


/* ============================================================
   VEHICLE DROPDOWN
============================================================ */

function populateVehicleSelect() {

    const select =
        elements.vehicle;

    if (!select) {
        return;
    }

    const filteredVehicles =
        getFilteredVehicles();

    select.innerHTML = "";

    if (filteredVehicles.length === 0) {

        addPlaceholder(
            select,
            "No matching vehicle"
        );

        return;

    }

    addPlaceholder(
        select,
        "Select vehicle model"
    );

    filteredVehicles.forEach(
        vehicle => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                vehicle.id;

            option.textContent =
                buildVehicleLabel(
                    vehicle
                );

            option.dataset.vehicleId =
                vehicle.id;

            option.dataset.categoryId =
                vehicle.category_id;

            option.dataset.energyId =
                vehicle.energy_source_id;

            if (
                vehicle.seating_capacity !==
                null &&
                vehicle.seating_capacity !==
                undefined
            ) {

                option.dataset.seating =
                    vehicle.seating_capacity;

            }

            select.appendChild(
                option
            );

        }
    );

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
            vehicles.filter(
                vehicle =>
                    Number(
                        vehicle.category_id
                    ) ===
                    Number(
                        category.id
                    )
            );

    }

    if (energy) {

        vehicles =
            vehicles.filter(
                vehicle =>
                    Number(
                        vehicle.energy_source_id
                    ) ===
                    Number(
                        energy.id
                    )
            );

    }

    if (seating !== null) {

        vehicles =
            vehicles.filter(
                vehicle => {

                    if (
                        vehicle.seating_capacity ===
                        null ||
                        vehicle.seating_capacity ===
                        undefined
                    ) {

                        return true;

                    }

                    return Number(
                        vehicle.seating_capacity
                    ) ===
                    Number(seating);

                }
            );

    }

    return vehicles;

}


/* ============================================================
   VEHICLE LABEL
============================================================ */

function buildVehicleLabel(
    vehicle
) {

    let label =
        vehicle.name ||
        "Vehicle";

    if (
        vehicle.seating_capacity !==
        null &&
        vehicle.seating_capacity !==
        undefined
    ) {

        label +=
            ` — ${vehicle.seating_capacity} seats`;

    }

    return label;

}


/* ============================================================
   PLACEHOLDER
============================================================ */

function addPlaceholder(
    select,
    text
) {

    const option =
        document.createElement(
            "option"
        );

    option.value = "";

    option.textContent =
        text;

    option.disabled = true;

    option.selected = true;

    select.appendChild(
        option
    );

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

    if (elements.fareForm) {

        elements.fareForm.addEventListener(
            "submit",
            event => {

                event.preventDefault();

                calculateFare();

            }
        );

    }

    if (elements.calculateBtn) {

        elements.calculateBtn.addEventListener(
            "click",
            event => {

                /*
                 * If the button is inside the form,
                 * the submit listener handles it.
                 */

                if (
                    !elements.fareForm
                ) {

                    event.preventDefault();

                    calculateFare();

                }

            }
        );

    }

    if (elements.resetBtn) {

        elements.resetBtn.addEventListener(
            "click",
            resetCalculator
        );

    }

    if (elements.retryBtn) {

        elements.retryBtn.addEventListener(
            "click",
            calculateFare
        );

    }

}


/* ============================================================
   CATEGORY CHANGE
============================================================ */

function handleCategoryChange() {

    state.selectedCategory =
        elements.category?.value ||
        null;

    state.selectedVehicle =
        null;

    state.selectedSeating =
        null;

    updateCategoryRequirements();

    updateSeatingOptions();

    populateVehicleSelect();

    clearFareResult();

}


/* ============================================================
   ENERGY CHANGE
============================================================ */

function handleEnergyChange() {

    state.selectedEnergy =
        elements.energy?.value ||
        null;

    state.selectedVehicle =
        null;

    populateVehicleSelect();

    clearFareResult();

}


/* ============================================================
   SEATING CHANGE
============================================================ */

function handleSeatingChange() {

    state.selectedSeating =
        getSelectedSeating();

    state.selectedVehicle =
        null;

    populateVehicleSelect();

    clearFareResult();

}


/* ============================================================
   VEHICLE CHANGE
============================================================ */

function handleVehicleChange() {

    const vehicleId =
        Number(
            elements.vehicle?.value
        );

    if (!vehicleId) {

        state.selectedVehicle =
            null;

        return;

    }

    state.selectedVehicle =
        state.vehicles.find(
            vehicle =>
                Number(
                    vehicle.id
                ) === vehicleId
        ) || null;

    /*
     * Automatically use the vehicle's seating
     * capacity when available.
     */

    if (
        state.selectedVehicle &&
        state.selectedVehicle
            .seating_capacity !==
            null
    ) {

        state.selectedSeating =
            Number(
                state.selectedVehicle
                    .seating_capacity
            );

    }

    clearFareResult();

}


/* ============================================================
   CATEGORY REQUIREMENTS
============================================================ */

function updateCategoryRequirements() {

    const category =
        getSelectedCategoryObject();

    if (!category) {

        setGroupVisible(
            elements.vehicleGroup,
            true
        );

        setGroupVisible(
            elements.seatingGroup,
            false
        );

        return;

    }

    const requiresModel =
        Boolean(
            category.requires_model
        );

    const requiresSeating =
        Boolean(
            category.requires_seating_capacity
        );

    setGroupVisible(
        elements.vehicleGroup,
        requiresModel
    );

    setGroupVisible(
        elements.seatingGroup,
        requiresSeating
    );

    if (elements.vehicle) {

        elements.vehicle.required =
            requiresModel;

    }

    if (elements.seating) {

        elements.seating.required =
            requiresSeating;

    }

}


/* ============================================================
   SET GROUP VISIBILITY
============================================================ */

function setGroupVisible(
    element,
    visible
) {

    if (!element) {
        return;
    }

    element.style.display =
        visible
            ? ""
            : "none";

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

    if (
        !category ||
        !category.requires_seating_capacity
    ) {

        select.innerHTML = "";

        addPlaceholder(
            select,
            "Select seats"
        );

        select.value = "";

        state.selectedSeating =
            null;

        return;

    }

    const capacities =
        [
            ...new Set(
                state.vehicles
                    .filter(
                        vehicle =>
                            Number(
                                vehicle.category_id
                            ) ===
                            Number(
                                category.id
                            )
                    )
                    .map(
                        vehicle =>
                            vehicle.seating_capacity
                    )
                    .filter(
                        value =>
                            value !==
                                null &&
                            value !==
                                undefined
                    )
            )
        ]
        .sort(
            (a, b) =>
                Number(a) -
                Number(b)
        );

    select.innerHTML = "";

    addPlaceholder(
        select,
        "Select seats"
    );

    capacities.forEach(
        capacity => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                capacity;

            option.textContent =
                `${capacity} seats`;

            select.appendChild(
                option
            );

        }
    );

}


/* ============================================================
   GET SELECTED CATEGORY
============================================================ */

function getSelectedCategoryObject() {

    if (
        !elements.category?.value
    ) {

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

    if (
        !elements.energy?.value
    ) {

        return null;

    }

    return state.energySources.find(
        energy =>
            energy.name ===
            elements.energy.value
    ) || null;

}


/* ============================================================
   GET SELECTED SEATING
============================================================ */

function getSelectedSeating() {

    if (
        !elements.seating ||
        !elements.seating.value
    ) {

        return null;

    }

    const value =
        Number(
            elements.seating.value
        );

    return Number.isFinite(value)
        ? value
        : null;

}


/* ============================================================
   CALCULATE FARE
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
        Number(
            elements.distance?.value
        );

    const seating =
        getSelectedSeating();

    const vehicleId =
        Number(
            elements.vehicle?.value
        ) || null;


    /* --------------------------------------------------------
       VALIDATION
    -------------------------------------------------------- */

    if (!category) {

        showCalculationError(
            "Please select a vehicle category."
        );

        elements.category?.focus();

        return;

    }


    if (!energy) {

        showCalculationError(
            "Please select a fuel or energy source."
        );

        elements.energy?.focus();

        return;

    }


    if (
        !Number.isFinite(distance) ||
        distance <= 0
    ) {

        showCalculationError(
            "Please enter a valid journey distance."
        );

        elements.distance?.focus();

        return;

    }


    if (
        category.requires_seating_capacity &&
        seating === null
    ) {

        showCalculationError(
            "Please select the seating capacity."
        );

        elements.seating?.focus();

        return;

    }


    /* --------------------------------------------------------
       BUILD REQUEST
    -------------------------------------------------------- */

    const requestBody = {

        category:
            category.name,

        energy_source:
            energy.name,

        distance_km:
            distance

    };


    /*
     * Only send seating when selected.
     */

    if (seating !== null) {

        requestBody.seating_capacity =
            seating;

    }


    /*
     * Send vehicle when selected.
     */

    if (vehicleId) {

        requestBody.vehicle_id =
            vehicleId;

    }


    console.log(
        "Fare calculation request:",
        requestBody
    );


    /* --------------------------------------------------------
       LOADING STATE
    -------------------------------------------------------- */

    state.loading = true;

    setCalculateLoading(true);

    showResultEmpty();


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


        if (
            !data ||
            data.success !== true ||
            !data.calculation
        ) {

            throw new Error(
                "The server returned an invalid fare calculation."
            );

        }


        state.lastCalculation =
            data.calculation;


        displayCalculation(
            data.calculation
        );


        showToast(
            "Fare calculated successfully."
        );


    } catch (error) {

        console.error(
            "Fare calculation failed:",
            error
        );

        showCalculationError(
            error.message ||
            "Unable to calculate fare."
        );

    } finally {

        state.loading =
            false;

        setCalculateLoading(
            false
        );

    }

}


/* ============================================================
   DISPLAY CALCULATION
============================================================ */

function displayCalculation(
    calculation
) {

    const fare =
        Number(
            calculation.fare
        );


    /* --------------------------------------------------------
       FARE
    -------------------------------------------------------- */

    if (elements.fareAmount) {

        elements.fareAmount.textContent =
            formatCurrencyNumber(
                fare
            );

    }


    /* --------------------------------------------------------
       CATEGORY
    -------------------------------------------------------- */

    if (elements.resultCategory) {

        elements.resultCategory.textContent =
            calculation.category ||
            "—";

    }


    /* --------------------------------------------------------
       ENERGY
    -------------------------------------------------------- */

    if (elements.resultEnergy) {

        elements.resultEnergy.textContent =
            calculation.energy_source ||
            "—";

    }


    /* --------------------------------------------------------
       DISTANCE
    -------------------------------------------------------- */

    if (elements.resultDistance) {

        elements.resultDistance.textContent =
            formatNumber(
                calculation.distance_km
            );

    }


    /* --------------------------------------------------------
       SEATING
    -------------------------------------------------------- */

    if (elements.resultSeats) {

        if (
            calculation.seating_capacity !==
                null &&
            calculation.seating_capacity !==
                undefined
        ) {

            elements.resultSeats.textContent =
                `${calculation.seating_capacity} seats`;

        } else {

            elements.resultSeats.textContent =
                "—";

        }

    }


    /* --------------------------------------------------------
       CALCULATION METHOD
    -------------------------------------------------------- */

    if (elements.calculationMethod) {

        elements.calculationMethod.textContent =
            formatCalculationMethod(
                calculation.calculation_method
            );

    }


    /* --------------------------------------------------------
       FARE RULE INFORMATION
    -------------------------------------------------------- */

    if (elements.fareRuleNote) {

        elements.fareRuleNote.textContent =
            buildFareRuleNote(
                calculation
            );

    }


    /* --------------------------------------------------------
       SHOW SUCCESS
    -------------------------------------------------------- */

    showResultSuccess();

}


/* ============================================================
   BUILD FARE RULE NOTE
============================================================ */

function buildFareRuleNote(
    calculation
) {

    const parts = [];


    if (
        calculation.government_reference
    ) {

        parts.push(
            `Reference: ${calculation.government_reference}.`
        );

    }


    if (
        calculation.minimum_fare !==
            null &&
        calculation.minimum_distance_km !==
            null
    ) {

        parts.push(
            `Minimum fare ₹${formatNumber(
                calculation.minimum_fare
            )} for the first ${formatNumber(
                calculation.minimum_distance_km
            )} km.`
        );

    }


    if (
        calculation.additional_distance_km !==
            null &&
        calculation.additional_fare !==
            null
    ) {

        parts.push(
            `Additional distance: ${formatNumber(
                calculation.additional_distance_km
            )} km, adding ₹${formatNumber(
                calculation.additional_fare
            )}.`
        );

    }


    if (
        parts.length === 0
    ) {

        return "Calculated using the applicable fare rule available in the Fare Keralam database.";

    }


    return parts.join(" ");

}


/* ============================================================
   CALCULATION METHOD FORMATTER
============================================================ */

function formatCalculationMethod(
    method
) {

    if (!method) {

        return "Database fare rule";

    }

    return method
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            letter =>
                letter.toUpperCase()
        );

}


/* ============================================================
   NUMBER FORMATTING
============================================================ */

function formatNumber(
    value
) {

    const number =
        Number(value);

    if (
        !Number.isFinite(number)
    ) {

        return "0.00";

    }

    return number.toLocaleString(
        "en-IN",
        {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }
    );

}


/* ============================================================
   CURRENCY NUMBER
============================================================ */

function formatCurrencyNumber(
    value
) {

    const number =
        Number(value);

    if (
        !Number.isFinite(number)
    ) {

        return "0.00";

    }

    return number.toLocaleString(
        "en-IN",
        {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }
    );

}


/* ============================================================
   RESULT STATES
============================================================ */

function showResultEmpty() {

    if (elements.resultEmpty) {

        elements.resultEmpty.style.display =
            "";

    }

    if (elements.resultSuccess) {

        elements.resultSuccess.style.display =
            "none";

    }

    if (elements.resultError) {

        elements.resultError.style.display =
            "none";

    }

}


function showResultSuccess() {

    if (elements.resultEmpty) {

        elements.resultEmpty.style.display =
            "none";

    }

    if (elements.resultSuccess) {

        elements.resultSuccess.style.display =
            "";

    }

    if (elements.resultError) {

        elements.resultError.style.display =
            "none";

    }

    elements.resultCard?.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
    });

}


function showCalculationError(
    message
) {

    if (elements.errorMessage) {

        elements.errorMessage.textContent =
            message;

    }

    if (elements.resultEmpty) {

        elements.resultEmpty.style.display =
            "none";

    }

    if (elements.resultSuccess) {

        elements.resultSuccess.style.display =
            "none";

    }

    if (elements.resultError) {

        elements.resultError.style.display =
            "";

    }

}


function clearFareResult() {

    state.lastCalculation =
        null;

    showResultEmpty();

    clearError();

}


function clearError() {

    if (elements.errorMessage) {

        elements.errorMessage.textContent =
            "Something went wrong. Please try again.";

    }

}


/* ============================================================
   CALCULATE BUTTON LOADING
============================================================ */

function setCalculateLoading(
    loading
) {

    const button =
        elements.calculateBtn;

    if (!button) {
        return;
    }

    button.disabled =
        loading;

    button.classList.toggle(
        "loading",
        loading
    );


    const buttonText =
        button.querySelector(
            ".button-text"
        );

    const buttonLoader =
        button.querySelector(
            ".button-loader"
        );


    if (buttonText) {

        buttonText.style.display =
            loading
                ? "none"
                : "";

    }


    if (buttonLoader) {

        buttonLoader.style.display =
            loading
                ? "inline-flex"
                : "none";

    }

}


/* ============================================================
   RESET CALCULATOR
============================================================ */

function resetCalculator() {

    if (elements.fareForm) {

        elements.fareForm.reset();

    }

    state.selectedCategory =
        null;

    state.selectedEnergy =
        null;

    state.selectedVehicle =
        null;

    state.selectedSeating =
        null;

    state.lastCalculation =
        null;


    if (elements.category) {

        elements.category.selectedIndex =
            0;

    }


    if (elements.energy) {

        elements.energy.selectedIndex =
            0;

    }


    if (elements.vehicle) {

        elements.vehicle.innerHTML =
            "";

        addPlaceholder(
            elements.vehicle,
            "Select vehicle model"
        );

    }


    updateCategoryRequirements();

    updateSeatingOptions();

    showResultEmpty();

    clearError();

    elements.distance?.focus();

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
             * Prevent negative values.
             */

            if (
                Number(
                    elements.distance.value
                ) < 0
            ) {

                elements.distance.value =
                    "";

            }

            /*
             * Remove stale result after
             * changing distance.
             */

            if (
                state.lastCalculation
            ) {

                clearFareResult();

            }

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

    updateCategoryRequirements();

    updateSeatingOptions();

    populateVehicleSelect();

}


/* ============================================================
   STATISTICS
============================================================ */

function updateStatistics() {

    const categoryCount =
        state.categories.length;

    const energyCount =
        state.energySources.length;

    const vehicleCount =
        state.vehicles.length;


    if (elements.categoryCount) {

        elements.categoryCount.textContent =
            categoryCount;

    }


    if (elements.energyCount) {

        elements.energyCount.textContent =
            energyCount;

    }


    if (elements.vehicleCountStat) {

        elements.vehicleCountStat.textContent =
            vehicleCount;

    }


    if (elements.vehicleCount) {

        elements.vehicleCount.textContent =
            `${vehicleCount}+`;

    }

}


/* ============================================================
   FOOTER STATUS
============================================================ */

function setFooterStatus(
    message,
    online
) {

    if (
        elements.footerStatus
    ) {

        elements.footerStatus.textContent =
            message;

    }

    const statusDot =
        document.querySelector(
            ".status-dot"
        );

    if (statusDot) {

        statusDot.classList.toggle(
            "offline",
            !online
        );

    }

}


/* ============================================================
   PAGE LOADER
============================================================ */

function showPageLoader(
    visible
) {

    if (
        !elements.pageLoader
    ) {

        return;

    }

    if (visible) {

        elements.pageLoader.classList.remove(
            "hidden"
        );

    } else {

        elements.pageLoader.classList.add(
            "hidden"
        );

    }

}


/* ============================================================
   GENERIC LOADING
============================================================ */

function showLoading(
    loading
) {

    state.loading =
        loading;

}


/* ============================================================
   MOBILE NAVIGATION
============================================================ */

function setupNavigation() {

    if (
        !elements.mobileMenuBtn ||
        !elements.mainNav
    ) {

        return;

    }


    elements.mobileMenuBtn.addEventListener(
        "click",
        () => {

            elements.mainNav.classList.toggle(
                "open"
            );

            const isOpen =
                elements.mainNav.classList.contains(
                    "open"
                );

            elements.mobileMenuBtn.setAttribute(
                "aria-label",
                isOpen
                    ? "Close navigation"
                    : "Open navigation"
            );

            const icon =
                elements.mobileMenuBtn.querySelector(
                    "i"
                );

            if (icon) {

                icon.className =
                    isOpen
                        ? "fa-solid fa-xmark"
                        : "fa-solid fa-bars";

            }

        }
    );


    $all(
        "#mainNav a"
    ).forEach(
        link => {

            link.addEventListener(
                "click",
                () => {

                    elements.mainNav.classList.remove(
                        "open"
                    );

                    const icon =
                        elements.mobileMenuBtn.querySelector(
                            "i"
                        );

                    if (icon) {

                        icon.className =
                            "fa-solid fa-bars";

                    }

                }
            );

        }
    );


    window.addEventListener(
        "scroll",
        updateActiveNavigation,
        {
            passive: true
        }
    );


    window.addEventListener(
        "scroll",
        updateHeader,
        {
            passive: true
        }
    );

}


/* ============================================================
   ACTIVE NAVIGATION
============================================================ */

function updateActiveNavigation() {

    const sections =
        $all(
            "main section[id]"
        );

    const links =
        $all(
            ".nav-link"
        );

    let current =
        "home";

    const scrollPosition =
        window.scrollY + 150;


    sections.forEach(
        section => {

            if (
                scrollPosition >=
                section.offsetTop
            ) {

                current =
                    section.id;

            }

        }
    );


    links.forEach(
        link => {

            const href =
                link.getAttribute(
                    "href"
                );

            link.classList.toggle(
                "active",
                href ===
                `#${current}`
            );

        }
    );

}


/* ============================================================
   HEADER SCROLL EFFECT
============================================================ */

function updateHeader() {

    if (!elements.header) {
        return;
    }

    elements.header.classList.toggle(
        "scrolled",
        window.scrollY > 30
    );

}


/* ============================================================
   CURRENT YEAR
============================================================ */

function setCurrentYear() {

    if (
        elements.currentYear
    ) {

        elements.currentYear.textContent =
            new Date().getFullYear();

    }

}


/* ============================================================
   TOAST
============================================================ */

let toastTimer = null;

function showToast(
    message
) {

    if (
        !elements.toast
    ) {

        return;

    }

    if (
        elements.toastMessage
    ) {

        elements.toastMessage.textContent =
            message;

    }

    elements.toast.classList.add(
        "show"
    );


    clearTimeout(
        toastTimer
    );


    toastTimer =
        setTimeout(
            () => {

                elements.toast.classList.remove(
                    "show"
                );

            },
            3000
        );

}


/* ============================================================
   EXPOSE OPTIONAL DEBUG STATE
============================================================ */

window.FareKeralam = {
    state,
    API,
    calculateFare,
    resetCalculator,
    checkAPIHealth
};


/* ============================================================
   END
============================================================ */