"use strict";

/* ============================================================
   FARE KERALAM — FRONTEND SCRIPT
   Backend: https://farekeralam.onrender.com
============================================================ */

const API_BASE_URL = "https://farekeralam.onrender.com/api";

const API = {
    health: `${API_BASE_URL}/health`,
    categories: `${API_BASE_URL}/categories`,
    energySources: `${API_BASE_URL}/energy-sources`,
    vehicles: `${API_BASE_URL}/vehicles`,
    vehicleOptions: `${API_BASE_URL}/vehicle-options`,
    calculate: `${API_BASE_URL}/fare/calculate`
};


/* ============================================================
   APPLICATION STATE
============================================================ */

const state = {
    categories: [],
    energySources: [],
    vehicles: [],
    lastCalculation: null,
    loading: false
};


/* ============================================================
   DOM HELPERS
============================================================ */

const $ = selector => document.querySelector(selector);

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
    resultVehicle: $("#resultVehicle"),

    calculationMethod: $("#calculationMethod"),
    fareRuleNote: $("#fareRuleNote"),

    minimumFare: $("#minimumFare"),
    additionalDistance: $("#additionalDistance"),
    additionalFare: $("#additionalFare"),

    slabSection: $("#slabSection"),
    slabBreakdown: $("#slabBreakdown"),

    resetBtn: $("#resetBtn"),
    retryBtn: $("#retryBtn"),

    errorMessage: $("#errorMessage"),

    footerStatus: $("#footerStatus"),
    footerStatusDot: $("#footerStatusDot"),

    currentYear: $("#currentYear"),

    categoryCount: $("#categoryCount"),
    energyCount: $("#energyCount"),
    vehicleCount: $("#vehicleCount"),
    vehicleCountStat: $("#vehicleCountStat"),

    toast: $("#toast"),
    toastMessage: $("#toastMessage"),

    heroApiStatus: $("#heroApiStatus"),
    heroVehicle: $("#heroVehicle"),
    heroDistance: $("#heroDistance"),
    heroFare: $("#heroFare"),
    heroEnergy: $("#heroEnergy")
};


/* ============================================================
   INITIALIZATION
============================================================ */

document.addEventListener("DOMContentLoaded", init);

async function init() {

    setCurrentYear();

    setupNavigation();

    setupEvents();

    setupDistanceInput();

    showResultEmpty();

    try {

        showPageLoader(true);

        await checkAPIHealth();

        await Promise.all([
            loadCategories(),
            loadEnergySources(),
            loadVehicles()
        ]);

        updateStatistics();

        updateCategoryRequirements();

        updateSeatingOptions();

        populateVehicleSelect();

        setFooterStatus("API connected", true);

        updateHeroStatus(true);

        console.log("Fare Keralam initialized successfully.");

    } catch (error) {

        console.error("Initialization error:", error);

        setFooterStatus("API unavailable", false);

        updateHeroStatus(false);

        showCalculationError(
            "Unable to connect to the Fare Keralam backend. Please try again later."
        );

    } finally {

        setTimeout(() => {
            showPageLoader(false);
        }, 500);
    }
}


/* ============================================================
   API REQUEST
============================================================ */

async function apiRequest(url, options = {}) {

    const controller = new AbortController();

    const timeout = setTimeout(() => {
        controller.abort();
    }, 15000);

    try {

        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                "Accept": "application/json",
                ...(options.body
                    ? { "Content-Type": "application/json" }
                    : {}),
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

            let message = `Server error (${response.status})`;

            if (data?.detail) {

                if (typeof data.detail === "string") {
                    message = data.detail;
                }

                else if (typeof data.detail === "object") {
                    message =
                        data.detail.message ||
                        data.detail.detail ||
                        message;
                }
            }

            throw new Error(message);
        }

        return data;

    } catch (error) {

        if (error.name === "AbortError") {
            throw new Error("The server took too long to respond.");
        }

        throw error;

    } finally {

        clearTimeout(timeout);
    }
}


/* ============================================================
   API HEALTH
============================================================ */

async function checkAPIHealth() {

    const data = await apiRequest(API.health);

    console.log("API health:", data);

    if (data?.status !== "healthy") {
        throw new Error("Backend API is not healthy.");
    }

    return data;
}


/* ============================================================
   LOAD CATEGORIES
============================================================ */

async function loadCategories() {

    const data = await apiRequest(API.categories);

    console.log("Categories response:", data);

    state.categories = Array.isArray(data?.categories)
        ? data.categories
        : [];

    populateCategorySelect();
}


/* ============================================================
   LOAD ENERGY SOURCES
============================================================ */

async function loadEnergySources() {

    const data = await apiRequest(API.energySources);

    console.log("Energy response:", data);

    state.energySources = Array.isArray(data?.energy_sources)
        ? data.energy_sources
        : [];

    populateEnergySelect();
}


/* ============================================================
   LOAD VEHICLES
============================================================ */

async function loadVehicles() {

    const data = await apiRequest(API.vehicles);

    console.log("Vehicles response:", data);

    state.vehicles = Array.isArray(data?.vehicles)
        ? data.vehicles
        : [];

    populateVehicleSelect();
}


/* ============================================================
   CATEGORY DROPDOWN
============================================================ */

function populateCategorySelect() {

    const select = elements.category;

    if (!select) return;

    select.innerHTML = "";

    addPlaceholder(
        select,
        "Select vehicle category"
    );

    state.categories.forEach(category => {

        const option = document.createElement("option");

        option.value = category.name;

        option.textContent = category.name;

        option.dataset.id = category.id;

        option.dataset.requiresModel =
            category.requires_model;

        option.dataset.requiresSeating =
            category.requires_seating_capacity;

        select.appendChild(option);
    });
}


/* ============================================================
   ENERGY DROPDOWN
============================================================ */

function populateEnergySelect() {

    const select = elements.energy;

    if (!select) return;

    select.innerHTML = "";

    addPlaceholder(
        select,
        "Select fuel / energy"
    );

    state.energySources.forEach(energy => {

        const option = document.createElement("option");

        option.value = energy.name;

        option.textContent = energy.name;

        option.dataset.id = energy.id;

        select.appendChild(option);
    });
}


/* ============================================================
   VEHICLE DROPDOWN
============================================================ */

function populateVehicleSelect() {

    const select = elements.vehicle;

    if (!select) return;

    const vehicles = getFilteredVehicles();

    select.innerHTML = "";

    addPlaceholder(
        select,
        vehicles.length
            ? "Select vehicle model"
            : "No matching vehicle"
    );

    vehicles.forEach(vehicle => {

        const option = document.createElement("option");

        option.value = vehicle.id;

        option.textContent = buildVehicleLabel(vehicle);

        option.dataset.vehicleId = vehicle.id;

        option.dataset.categoryId =
            vehicle.category_id;

        option.dataset.energyId =
            vehicle.energy_source_id;

        select.appendChild(option);
    });
}


/* ============================================================
   FILTER VEHICLES
============================================================ */

function getFilteredVehicles() {

    let vehicles = [...state.vehicles];

    const category = getSelectedCategory();

    const energy = getSelectedEnergy();

    const seating = getSelectedSeating();

    if (category) {

        vehicles = vehicles.filter(vehicle =>
            Number(vehicle.category_id) ===
            Number(category.id)
        );
    }

    if (energy) {

        vehicles = vehicles.filter(vehicle =>
            Number(vehicle.energy_source_id) ===
            Number(energy.id)
        );
    }

    if (seating !== null) {

        vehicles = vehicles.filter(vehicle => {

            if (
                vehicle.seating_capacity === null ||
                vehicle.seating_capacity === undefined
            ) {
                return true;
            }

            return Number(vehicle.seating_capacity) ===
                Number(seating);
        });
    }

    return vehicles;
}


/* ============================================================
   VEHICLE LABEL
============================================================ */

function buildVehicleLabel(vehicle) {

    let label = vehicle.name || "Vehicle";

    if (
        vehicle.seating_capacity !== null &&
        vehicle.seating_capacity !== undefined
    ) {

        label += ` — ${vehicle.seating_capacity} seats`;
    }

    return label;
}


/* ============================================================
   PLACEHOLDER
============================================================ */

function addPlaceholder(select, text) {

    const option = document.createElement("option");

    option.value = "";

    option.textContent = text;

    option.disabled = true;

    option.selected = true;

    select.appendChild(option);
}


/* ============================================================
   EVENT LISTENERS
============================================================ */

function setupEvents() {

    elements.category?.addEventListener(
        "change",
        handleCategoryChange
    );

    elements.energy?.addEventListener(
        "change",
        handleEnergyChange
    );

    elements.seating?.addEventListener(
        "change",
        handleSeatingChange
    );

    elements.vehicle?.addEventListener(
        "change",
        handleVehicleChange
    );

    elements.fareForm?.addEventListener(
        "submit",
        event => {

            event.preventDefault();

            calculateFare();
        }
    );

    elements.resetBtn?.addEventListener(
        "click",
        resetCalculator
    );

    elements.retryBtn?.addEventListener(
        "click",
        calculateFare
    );
}


/* ============================================================
   CATEGORY CHANGE
============================================================ */

function handleCategoryChange() {

    updateCategoryRequirements();

    updateSeatingOptions();

    populateVehicleSelect();

    clearFareResult();
}


/* ============================================================
   ENERGY CHANGE
============================================================ */

function handleEnergyChange() {

    populateVehicleSelect();

    clearFareResult();
}


/* ============================================================
   SEATING CHANGE
============================================================ */

function handleSeatingChange() {

    populateVehicleSelect();

    clearFareResult();
}


/* ============================================================
   VEHICLE CHANGE
============================================================ */

function handleVehicleChange() {

    clearFareResult();
}


/* ============================================================
   CATEGORY REQUIREMENTS
============================================================ */

function updateCategoryRequirements() {

    const category = getSelectedCategory();

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
        category.requires_model === true ||
        category.requires_model === 1 ||
        category.requires_model === "true";

    const requiresSeating =
        category.requires_seating_capacity === true ||
        category.requires_seating_capacity === 1 ||
        category.requires_seating_capacity === "true";

    setGroupVisible(
        elements.vehicleGroup,
        requiresModel
    );

    setGroupVisible(
        elements.seatingGroup,
        requiresSeating
    );

    if (elements.vehicle) {
        elements.vehicle.required = requiresModel;
    }

    if (elements.seating) {
        elements.seating.required = requiresSeating;
    }
}


/* ============================================================
   GROUP VISIBILITY
============================================================ */

function setGroupVisible(element, visible) {

    if (!element) return;

    element.style.display = visible
        ? ""
        : "none";
}


/* ============================================================
   SEATING OPTIONS
============================================================ */

function updateSeatingOptions() {

    const select = elements.seating;

    if (!select) return;

    const category = getSelectedCategory();

    select.innerHTML = "";

    addPlaceholder(
        select,
        "Select seats"
    );

    if (
        !category ||
        !(
            category.requires_seating_capacity === true ||
            category.requires_seating_capacity === 1 ||
            category.requires_seating_capacity === "true"
        )
    ) {
        return;
    }

    const capacities = [
        ...new Set(
            state.vehicles
                .filter(vehicle =>
                    Number(vehicle.category_id) ===
                    Number(category.id)
                )
                .map(vehicle =>
                    vehicle.seating_capacity
                )
                .filter(value =>
                    value !== null &&
                    value !== undefined
                )
        )
    ].sort((a, b) => Number(a) - Number(b));

    capacities.forEach(capacity => {

        const option = document.createElement("option");

        option.value = capacity;

        option.textContent =
            `${capacity} seats`;

        select.appendChild(option);
    });
}


/* ============================================================
   SELECTED OBJECTS
============================================================ */

function getSelectedCategory() {

    const value = elements.category?.value;

    if (!value) return null;

    return state.categories.find(
        category => category.name === value
    ) || null;
}


function getSelectedEnergy() {

    const value = elements.energy?.value;

    if (!value) return null;

    return state.energySources.find(
        energy => energy.name === value
    ) || null;
}


function getSelectedSeating() {

    const value = elements.seating?.value;

    if (!value) return null;

    const number = Number(value);

    return Number.isFinite(number)
        ? number
        : null;
}


/* ============================================================
   CALCULATE FARE
============================================================ */

async function calculateFare() {

    if (state.loading) return;

    clearError();

    const category = getSelectedCategory();

    const energy = getSelectedEnergy();

    const distance = Number(
        elements.distance?.value
    );

    const seating = getSelectedSeating();

    const vehicleId =
        Number(elements.vehicle?.value) || null;


    /* VALIDATION */

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


    const requiresSeating =
        category.requires_seating_capacity === true ||
        category.requires_seating_capacity === 1 ||
        category.requires_seating_capacity === "true";


    if (
        requiresSeating &&
        seating === null
    ) {

        showCalculationError(
            "Please select the seating capacity."
        );

        elements.seating?.focus();

        return;
    }


    /* REQUEST */

    const requestBody = {

        category: category.name,

        energy_source: energy.name,

        distance_km: distance
    };


    if (seating !== null) {

        requestBody.seating_capacity =
            seating;
    }


    if (vehicleId) {

        requestBody.vehicle_id =
            vehicleId;
    }


    console.log(
        "Sending fare request:",
        requestBody
    );


    state.loading = true;

    setCalculateLoading(true);

    try {

        const response = await apiRequest(
            API.calculate,
            {
                method: "POST",
                body: JSON.stringify(requestBody)
            }
        );


        console.log(
            "Fare API response:",
            response
        );


        const calculation =
            response?.calculation ||
            response?.data ||
            response;


        if (!calculation) {

            throw new Error(
                "No calculation was returned by the server."
            );
        }


        state.lastCalculation =
            calculation;


        displayCalculation(
            calculation
        );


        showToast(
            "Fare calculated successfully."
        );


    } catch (error) {

        console.error(
            "Calculation error:",
            error
        );

        showCalculationError(
            error.message ||
            "Unable to calculate fare."
        );

    } finally {

        state.loading = false;

        setCalculateLoading(false);
    }
}


/* ============================================================
   DISPLAY CALCULATION
============================================================ */

function displayCalculation(calculation) {

    console.log(
        "Displaying calculation:",
        calculation
    );


    /* --------------------------------------------------------
       FARE
    -------------------------------------------------------- */

    const fare = firstNumber(
        calculation.fare,
        calculation.total_fare,
        calculation.amount,
        calculation.final_fare
    );


    if (elements.fareAmount) {

        elements.fareAmount.textContent =
            formatNumber(fare);
    }


    /* --------------------------------------------------------
       CATEGORY
    -------------------------------------------------------- */

    if (elements.resultCategory) {

        elements.resultCategory.textContent =
            calculation.category ||
            getSelectedCategory()?.name ||
            "—";
    }


    /* --------------------------------------------------------
       ENERGY
    -------------------------------------------------------- */

    if (elements.resultEnergy) {

        elements.resultEnergy.textContent =
            calculation.energy_source ||
            getSelectedEnergy()?.name ||
            "—";
    }


    /* --------------------------------------------------------
       DISTANCE
    -------------------------------------------------------- */

    const distance = firstNumber(
        calculation.distance_km,
        calculation.distance
    );


    if (elements.resultDistance) {

        elements.resultDistance.textContent =
            formatNumber(distance);
    }


    /* --------------------------------------------------------
       SEATING
    -------------------------------------------------------- */

    const seats =
        calculation.seating_capacity ??
        calculation.seats ??
        getSelectedSeating();


    if (elements.resultSeats) {

        elements.resultSeats.textContent =
            seats !== null &&
            seats !== undefined
                ? `${seats} seats`
                : "—";
    }


    /* --------------------------------------------------------
       VEHICLE
    -------------------------------------------------------- */

    const selectedVehicle =
        state.vehicles.find(
            vehicle =>
                Number(vehicle.id) ===
                Number(elements.vehicle?.value)
        );


    if (elements.resultVehicle) {

        elements.resultVehicle.textContent =
            calculation.vehicle_name ||
            calculation.vehicle ||
            selectedVehicle?.name ||
            "—";
    }


    /* --------------------------------------------------------
       CALCULATION METHOD
    -------------------------------------------------------- */

    if (elements.calculationMethod) {

        elements.calculationMethod.textContent =
            formatCalculationMethod(
                calculation.calculation_method ||
                calculation.method
            );
    }


    /* --------------------------------------------------------
       BREAKDOWN
    -------------------------------------------------------- */

    const minimumFare = firstNumber(
        calculation.minimum_fare,
        calculation.base_fare,
        calculation.min_fare
    );


    const additionalDistance = firstNumber(
        calculation.additional_distance_km,
        calculation.extra_distance_km,
        calculation.additional_distance
    );


    const additionalFare = firstNumber(
        calculation.additional_fare,
        calculation.extra_fare
    );


    if (elements.minimumFare) {

        elements.minimumFare.textContent =
            formatNumber(minimumFare);
    }


    if (elements.additionalDistance) {

        elements.additionalDistance.textContent =
            formatNumber(additionalDistance);
    }


    if (elements.additionalFare) {

        elements.additionalFare.textContent =
            formatNumber(additionalFare);
    }


    /* --------------------------------------------------------
       SLABS
    -------------------------------------------------------- */

    renderSlabs(
        calculation.slabs ||
        calculation.fare_slabs ||
        calculation.breakdown ||
        []
    );


    /* --------------------------------------------------------
       RULE NOTE
    -------------------------------------------------------- */

    if (elements.fareRuleNote) {

        elements.fareRuleNote.textContent =
            buildFareRuleNote(calculation);
    }


    /* --------------------------------------------------------
       HERO
    -------------------------------------------------------- */

    updateHeroCalculation(
        calculation
    );


    /* --------------------------------------------------------
       SHOW RESULT
    -------------------------------------------------------- */

    showResultSuccess();
}


/* ============================================================
   RENDER SLABS
============================================================ */

function renderSlabs(slabs) {

    if (
        !elements.slabSection ||
        !elements.slabBreakdown
    ) {
        return;
    }


    if (!Array.isArray(slabs) || slabs.length === 0) {

        elements.slabSection.style.display =
            "none";

        elements.slabBreakdown.innerHTML =
            "";

        return;
    }


    elements.slabSection.style.display =
        "";


    elements.slabBreakdown.innerHTML =
        "";


    slabs.forEach((slab, index) => {

        const row =
            document.createElement("div");

        row.className =
            "slab-row";


        const label =
            slab.label ||
            slab.description ||
            `Slab ${index + 1}`;


        const amount =
            firstNumber(
                slab.fare,
                slab.amount,
                slab.price
            );


        row.innerHTML = `
            <span>${escapeHTML(label)}</span>
            <strong>₹${formatNumber(amount)}</strong>
        `;


        elements.slabBreakdown.appendChild(row);
    });
}


/* ============================================================
   FARE RULE NOTE
============================================================ */

function buildFareRuleNote(calculation) {

    const parts = [];


    if (calculation.government_reference) {

        parts.push(
            `Reference: ${calculation.government_reference}.`
        );
    }


    const minimumFare =
        firstNumber(
            calculation.minimum_fare
        );


    const minimumDistance =
        firstNumber(
            calculation.minimum_distance_km
        );


    if (
        minimumFare !== null &&
        minimumDistance !== null
    ) {

        parts.push(
            `Minimum fare ₹${formatNumber(
                minimumFare
            )} for the first ${formatNumber(
                minimumDistance
            )} km.`
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
   NUMBER HELPER
============================================================ */

function firstNumber(...values) {

    for (const value of values) {

        if (
            value !== null &&
            value !== undefined &&
            value !== "" &&
            Number.isFinite(Number(value))
        ) {

            return Number(value);
        }
    }

    return 0;
}


/* ============================================================
   FORMAT NUMBER
============================================================ */

function formatNumber(value) {

    const number = Number(value);

    if (!Number.isFinite(number)) {
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
   CALCULATION METHOD
============================================================ */

function formatCalculationMethod(method) {

    if (!method) {
        return "Database fare rule";
    }

    return String(method)
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            letter => letter.toUpperCase()
        );
}


/* ============================================================
   RESULT STATES
============================================================ */

function showResultEmpty() {

    elements.resultEmpty?.style &&
        (elements.resultEmpty.style.display = "");

    elements.resultSuccess?.style &&
        (elements.resultSuccess.style.display = "none");

    elements.resultError?.style &&
        (elements.resultError.style.display = "none");
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


function showCalculationError(message) {

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

    state.lastCalculation = null;

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
   BUTTON LOADING
============================================================ */

function setCalculateLoading(loading) {

    const button =
        elements.calculateBtn;

    if (!button) return;


    button.disabled =
        loading;


    button.classList.toggle(
        "loading",
        loading
    );


    const text =
        button.querySelector(
            ".button-text"
        );


    const loader =
        button.querySelector(
            ".button-loader"
        );


    const arrow =
        button.querySelector(
            ".button-arrow"
        );


    if (text) {
        text.style.display =
            loading ? "none" : "";
    }


    if (loader) {
        loader.style.display =
            loading ? "inline-flex" : "none";
    }


    if (arrow) {
        arrow.style.display =
            loading ? "none" : "";
    }
}


/* ============================================================
   RESET
============================================================ */

function resetCalculator() {

    elements.fareForm?.reset();

    state.lastCalculation = null;

    showResultEmpty();

    clearError();

    updateCategoryRequirements();

    updateSeatingOptions();

    populateVehicleSelect();

    if (elements.heroFare) {
        elements.heroFare.textContent =
            "—";
    }

    if (elements.heroVehicle) {
        elements.heroVehicle.textContent =
            "Auto Rickshaw";
    }

    if (elements.heroDistance) {
        elements.heroDistance.textContent =
            "—";
    }

    if (elements.heroEnergy) {
        elements.heroEnergy.textContent =
            "—";
    }
}


/* ============================================================
   DISTANCE INPUT
============================================================ */

function setupDistanceInput() {

    const input =
        elements.distance;

    if (!input) return;


    input.addEventListener(
        "input",
        () => {

            if (
                Number(input.value) < 0
            ) {
                input.value = "";
            }

            if (
                state.lastCalculation
            ) {
                clearFareResult();
            }
        }
    );
}


/* ============================================================
   STATISTICS
============================================================ */

function updateStatistics() {

    if (elements.categoryCount) {

        elements.categoryCount.textContent =
            state.categories.length;
    }


    if (elements.energyCount) {

        elements.energyCount.textContent =
            state.energySources.length;
    }


    if (elements.vehicleCountStat) {

        elements.vehicleCountStat.textContent =
            state.vehicles.length;
    }


    if (elements.vehicleCount) {

        elements.vehicleCount.textContent =
            `${state.vehicles.length}+`;
    }
}


/* ============================================================
   FOOTER STATUS
============================================================ */

function setFooterStatus(message, online) {

    if (elements.footerStatus) {

        elements.footerStatus.textContent =
            message;
    }


    if (elements.footerStatusDot) {

        elements.footerStatusDot.classList.toggle(
            "offline",
            !online
        );
    }
}


/* ============================================================
   HERO API STATUS
============================================================ */

function updateHeroStatus(online) {

    if (!elements.heroApiStatus) {
        return;
    }


    elements.heroApiStatus.classList.toggle(
        "offline",
        !online
    );


    const text =
        elements.heroApiStatus.lastChild;


    if (text && text.nodeType === 3) {

        text.textContent =
            online ? " API" : " Offline";
    }
}


/* ============================================================
   HERO CALCULATION
============================================================ */

function updateHeroCalculation(calculation) {

    const fare = firstNumber(
        calculation.fare,
        calculation.total_fare,
        calculation.amount
    );


    if (elements.heroFare) {

        elements.heroFare.textContent =
            `₹${formatNumber(fare)}`;
    }


    if (elements.heroDistance) {

        const distance =
            firstNumber(
                calculation.distance_km,
                calculation.distance
            );

        elements.heroDistance.textContent =
            `${formatNumber(distance)} km`;
    }


    if (elements.heroVehicle) {

        elements.heroVehicle.textContent =
            calculation.vehicle_name ||
            calculation.vehicle ||
            getSelectedVehicleName() ||
            "Vehicle";
    }


    if (elements.heroEnergy) {

        elements.heroEnergy.textContent =
            calculation.energy_source ||
            getSelectedEnergy()?.name ||
            "—";
    }
}


/* ============================================================
   SELECTED VEHICLE
============================================================ */

function getSelectedVehicleName() {

    const id =
        Number(elements.vehicle?.value);

    if (!id) return null;

    const vehicle =
        state.vehicles.find(
            item =>
                Number(item.id) === id
        );

    return vehicle?.name || null;
}


/* ============================================================
   MOBILE NAVIGATION
============================================================ */

function setupNavigation() {

    const button =
        elements.mobileMenuBtn;

    const nav =
        elements.mainNav;


    if (!button || !nav) return;


    button.addEventListener(
        "click",
        () => {

            nav.classList.toggle("open");

            const open =
                nav.classList.contains("open");


            button.setAttribute(
                "aria-label",
                open
                    ? "Close navigation"
                    : "Open navigation"
            );


            const icon =
                button.querySelector("i");


            if (icon) {

                icon.className =
                    open
                        ? "fa-solid fa-xmark"
                        : "fa-solid fa-bars";
            }
        }
    );


    document.querySelectorAll(
        "#mainNav a"
    ).forEach(link => {

        link.addEventListener(
            "click",
            () => {

                nav.classList.remove("open");

                const icon =
                    button.querySelector("i");

                if (icon) {
                    icon.className =
                        "fa-solid fa-bars";
                }
            }
        );
    });


    window.addEventListener(
        "scroll",
        updateHeader,
        { passive: true }
    );
}


/* ============================================================
   HEADER
============================================================ */

function updateHeader() {

    if (!elements.header) return;

    elements.header.classList.toggle(
        "scrolled",
        window.scrollY > 30
    );
}


/* ============================================================
   CURRENT YEAR
============================================================ */

function setCurrentYear() {

    if (elements.currentYear) {

        elements.currentYear.textContent =
            new Date().getFullYear();
    }
}


/* ============================================================
   PAGE LOADER
============================================================ */

function showPageLoader(visible) {

    if (!elements.pageLoader) return;

    elements.pageLoader.classList.toggle(
        "hidden",
        !visible
    );
}


/* ============================================================
   TOAST
============================================================ */

let toastTimer = null;

function showToast(message) {

    if (!elements.toast) return;


    if (elements.toastMessage) {

        elements.toastMessage.textContent =
            message;
    }


    elements.toast.classList.add("show");


    clearTimeout(toastTimer);


    toastTimer = setTimeout(
        () => {

            elements.toast.classList.remove(
                "show"
            );

        },
        3000
    );
}


/* ============================================================
   HTML ESCAPE
============================================================ */

function escapeHTML(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* ============================================================
   DEBUG API
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