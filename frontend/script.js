/* ============================================================
   FARE KERALAM
   FRONTEND JAVASCRIPT
============================================================ */

"use strict";


/* ============================================================
   CONFIGURATION
============================================================ */

const API_BASE =
    "https://farekeralam.onrender.com";


/* ============================================================
   DOM
============================================================ */

const pageLoader =
    document.getElementById("pageLoader");

const siteHeader =
    document.getElementById("siteHeader");

const mobileMenuBtn =
    document.getElementById("mobileMenuBtn");

const mainNav =
    document.getElementById("mainNav");

const fareForm =
    document.getElementById("fareForm");

const categorySelect =
    document.getElementById("category");

const energySelect =
    document.getElementById("energy");

const seatingSelect =
    document.getElementById("seating");

const vehicleSelect =
    document.getElementById("vehicle");

const seatingGroup =
    document.getElementById("seatingGroup");

const vehicleGroup =
    document.getElementById("vehicleGroup");

const distanceInput =
    document.getElementById("distance");

const calculateBtn =
    document.getElementById("calculateBtn");

const resultCard =
    document.getElementById("resultCard");

const resultEmpty =
    document.getElementById("resultEmpty");

const resultSuccess =
    document.getElementById("resultSuccess");

const resultError =
    document.getElementById("resultError");

const fareAmount =
    document.getElementById("fareAmount");

const resultCategory =
    document.getElementById("resultCategory");

const resultEnergy =
    document.getElementById("resultEnergy");

const resultDistance =
    document.getElementById("resultDistance");

const resultSeats =
    document.getElementById("resultSeats");

const calculationMethod =
    document.getElementById("calculationMethod");

const fareRuleNote =
    document.getElementById("fareRuleNote");

const errorMessage =
    document.getElementById("errorMessage");

const resetBtn =
    document.getElementById("resetBtn");

const retryBtn =
    document.getElementById("retryBtn");

const toast =
    document.getElementById("toast");

const toastMessage =
    document.getElementById("toastMessage");

const currentYear =
    document.getElementById("currentYear");

const footerStatus =
    document.getElementById("footerStatus");

const categoryCount =
    document.getElementById("categoryCount");

const energyCount =
    document.getElementById("energyCount");

const vehicleCount =
    document.getElementById("vehicleCount");

const vehicleCountStat =
    document.getElementById("vehicleCountStat");


/* ============================================================
   STATE
============================================================ */

let categories = [];
let energySources = [];
let vehicles = [];

let lastCalculation = null;


/* ============================================================
   INITIALIZATION
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    init
);


async function init() {

    currentYear.textContent =
        new Date().getFullYear();

    setupNavigation();

    setupScrollEffects();

    setupForm();

    setupRevealAnimations();

    await loadInitialData();

    checkAPIStatus();

    setTimeout(() => {

        pageLoader.classList.add("hidden");

        document.body.classList.remove("loading");

    }, 500);
}


/* ============================================================
   NAVIGATION
============================================================ */

function setupNavigation() {

    mobileMenuBtn.addEventListener(
        "click",
        () => {

            mainNav.classList.toggle("open");

            const icon =
                mobileMenuBtn.querySelector("i");

            if (mainNav.classList.contains("open")) {

                icon.classList.remove(
                    "fa-bars"
                );

                icon.classList.add(
                    "fa-xmark"
                );

            } else {

                icon.classList.remove(
                    "fa-xmark"
                );

                icon.classList.add(
                    "fa-bars"
                );
            }

        }
    );


    document.querySelectorAll(
        ".nav-link, .main-nav a"
    ).forEach(link => {

        link.addEventListener(
            "click",
            () => {

                mainNav.classList.remove(
                    "open"
                );

                const icon =
                    mobileMenuBtn.querySelector("i");

                icon.classList.remove(
                    "fa-xmark"
                );

                icon.classList.add(
                    "fa-bars"
                );

            }
        );

    });


    document.querySelectorAll(
        'a[href^="#"]'
    ).forEach(link => {

        link.addEventListener(
            "click",
            event => {

                const targetId =
                    link.getAttribute("href");

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

            }
        );

    });

}


/* ============================================================
   SCROLL EFFECTS
============================================================ */

function setupScrollEffects() {

    window.addEventListener(
        "scroll",
        () => {

            if (window.scrollY > 30) {

                siteHeader.classList.add(
                    "scrolled"
                );

            } else {

                siteHeader.classList.remove(
                    "scrolled"
                );
            }

            updateActiveNavigation();

        },
        { passive: true }
    );

}


function updateActiveNavigation() {

    const sections =
        document.querySelectorAll(
            "main section[id]"
        );

    const scrollPosition =
        window.scrollY + 180;

    sections.forEach(section => {

        const top =
            section.offsetTop;

        const height =
            section.offsetHeight;

        const id =
            section.getAttribute("id");

        if (
            scrollPosition >= top &&
            scrollPosition < top + height
        ) {

            document
                .querySelectorAll(".nav-link")
                .forEach(link => {

                    link.classList.remove(
                        "active"
                    );

                });

            const active =
                document.querySelector(
                    `.nav-link[href="#${id}"]`
                );

            if (active) {
                active.classList.add(
                    "active"
                );
            }
        }

    });

}


/* ============================================================
   API
============================================================ */

async function apiFetch(
    endpoint,
    options = {}
) {

    const response =
        await fetch(
            `${API_BASE}${endpoint}`,
            {
                ...options,

                headers: {
                    "Accept":
                        "application/json",

                    "Content-Type":
                        "application/json",

                    ...(options.headers || {})
                }
            }
        );


    let data = null;

    try {

        data =
            await response.json();

    } catch {

        data = null;

    }


    if (!response.ok) {

        const message =
            extractAPIError(
                data,
                response.status
            );

        throw new Error(message);
    }


    return data;
}


function extractAPIError(
    data,
    status
) {

    if (!data) {

        return `Server returned HTTP ${status}.`;
    }

    if (
        typeof data.detail === "string"
    ) {

        return data.detail;
    }

    if (
        data.detail &&
        typeof data.detail.message === "string"
    ) {

        return data.detail.message;
    }

    if (
        typeof data.message === "string"
    ) {

        return data.message;
    }

    return `Server returned HTTP ${status}.`;
}


/* ============================================================
   INITIAL DATA
============================================================ */

async function loadInitialData() {

    try {

        const [
            categoryData,
            energyData,
            vehicleData
        ] = await Promise.all([

            apiFetch(
                "/api/categories"
            ),

            apiFetch(
                "/api/energy-sources"
            ),

            apiFetch(
                "/api/vehicles"
            )

        ]);


        categories =
            categoryData.categories || [];

        energySources =
            energyData.energy_sources || [];

        vehicles =
            vehicleData.vehicles || [];


        populateCategories();

        populateEnergySources();

        updateStats();


    } catch (error) {

        console.error(
            "Initial API loading failed:",
            error
        );

        /*
         * Keep the frontend usable even if
         * the API temporarily takes time to
         * wake up on Render.
         */

        showToast(
            "Backend is waking up. Please try again shortly."
        );

    }

}


/* ============================================================
   CATEGORIES
============================================================ */

function populateCategories() {

    categorySelect.innerHTML = `
        <option value="">
            Select vehicle category
        </option>
    `;


    categories.forEach(category => {

        const option =
            document.createElement(
                "option"
            );

        option.value =
            category.name;

        option.textContent =
            category.name;

        option.dataset.requiresModel =
            category.requires_model;

        option.dataset.requiresSeating =
            category.requires_seating_capacity;

        categorySelect.appendChild(
            option
        );

    });

}


/* ============================================================
   ENERGY SOURCES
============================================================ */

function populateEnergySources() {

    energySelect.innerHTML = `
        <option value="">
            Select energy
        </option>
    `;


    energySources.forEach(
        energy => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                energy.name;

            option.textContent =
                energy.name;

            energySelect.appendChild(
                option
            );

        }
    );

}


/* ============================================================
   CATEGORY CHANGE
============================================================ */

categorySelect.addEventListener(
    "change",
    handleCategoryChange
);


function handleCategoryChange() {

    const categoryName =
        categorySelect.value;

    const category =
        categories.find(
            item =>
                item.name === categoryName
        );


    if (!category) {

        resetDependentFields();

        return;
    }


    updateVehicleModels();

    updateSeatingOptions();


    /*
     * Vehicle model is only required
     * for categories that need it.
     */

    if (category.requires_model) {

        vehicleGroup.style.display =
            "block";

    } else {

        vehicleGroup.style.display =
            "none";

        vehicleSelect.value =
            "";

    }


    /*
     * Seating capacity
     */

    if (
        category.requires_seating_capacity
    ) {

        seatingGroup.style.display =
            "block";

    } else {

        seatingGroup.style.display =
            "none";

        seatingSelect.value =
            "";

    }

}


/* ============================================================
   ENERGY CHANGE
============================================================ */

energySelect.addEventListener(
    "change",
    () => {

        updateVehicleModels();

        updateSeatingOptions();

    }
);


/* ============================================================
   SEATING CHANGE
============================================================ */

seatingSelect.addEventListener(
    "change",
    () => {

        updateVehicleModels();

    }
);


/* ============================================================
   UPDATE VEHICLES
============================================================ */

function updateVehicleModels() {

    const category =
        categorySelect.value;

    const energy =
        energySelect.value;

    const seating =
        seatingSelect.value;


    vehicleSelect.innerHTML = `
        <option value="">
            Select vehicle model
        </option>
    `;


    if (!category) {
        return;
    }


    const categoryObject =
        categories.find(
            item =>
                item.name === category
        );


    let filtered =
        vehicles.filter(
            vehicle => {

                /*
                 * Vehicle category
                 */

                const matchesCategory =
                    getCategoryName(
                        vehicle.category_id
                    ) === category;

                if (!matchesCategory) {
                    return false;
                }


                /*
                 * Energy
                 */

                if (energy) {

                    const energyName =
                        getEnergyName(
                            vehicle.energy_source_id
                        );

                    if (
                        energyName !== energy
                    ) {
                        return false;
                    }
                }


                /*
                 * Seating
                 */

                if (seating) {

                    if (
                        Number(
                            vehicle.seating_capacity
                        ) !== Number(seating)
                    ) {

                        return false;
                    }
                }


                return true;

            }
        );


    /*
     * Remove duplicate vehicle names.
     */

    const unique =
        new Map();

    filtered.forEach(
        vehicle => {

            if (
                !unique.has(
                    vehicle.name
                )
            ) {

                unique.set(
                    vehicle.name,
                    vehicle
                );
            }

        }
    );


    Array.from(
        unique.values()
    ).forEach(
        vehicle => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                vehicle.id;

            option.textContent =
                vehicle.name;

            vehicleSelect.appendChild(
                option
            );

        }
    );


    /*
     * If category requires a model but
     * none exists, show an informational
     * placeholder.
     */

    if (
        categoryObject &&
        categoryObject.requires_model &&
        unique.size === 0
    ) {

        vehicleSelect.innerHTML = `
            <option value="">
                No matching models available
            </option>
        `;

    }

}


/* ============================================================
   SEATING OPTIONS
============================================================ */

function updateSeatingOptions() {

    const category =
        categorySelect.value;

    const energy =
        energySelect.value;


    seatingSelect.innerHTML = `
        <option value="">
            Select seats
        </option>
    `;


    if (!category) {
        return;
    }


    let filtered =
        vehicles.filter(
            vehicle => {

                if (
                    getCategoryName(
                        vehicle.category_id
                    ) !== category
                ) {

                    return false;
                }


                if (energy) {

                    if (
                        getEnergyName(
                            vehicle.energy_source_id
                        ) !== energy
                    ) {

                        return false;
                    }

                }


                return (
                    vehicle.seating_capacity !==
                    null
                );

            }
        );


    const seats =
        [
            ...new Set(
                filtered.map(
                    vehicle =>
                        Number(
                            vehicle.seating_capacity
                        )
                )
            )
        ]
        .filter(
            value =>
                Number.isFinite(value)
        )
        .sort(
            (a,b) =>
                a - b
        );


    seats.forEach(
        seatsValue => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                seatsValue;

            option.textContent =
                `${seatsValue} seats`;

            seatingSelect.appendChild(
                option
            );

        }
    );

}


/* ============================================================
   DATABASE ID HELPERS
============================================================ */

function getCategoryName(
    categoryId
) {

    const category =
        categories.find(
            item =>
                Number(item.id) ===
                Number(categoryId)
        );

    return category
        ? category.name
        : null;
}


function getEnergyName(
    energyId
) {

    const energy =
        energySources.find(
            item =>
                Number(item.id) ===
                Number(energyId)
        );

    return energy
        ? energy.name
        : null;
}


/* ============================================================
   FORM
============================================================ */

function setupForm() {

    fareForm.addEventListener(
        "submit",
        handleFareCalculation
    );


    resetBtn.addEventListener(
        "click",
        resetCalculator
    );


    retryBtn.addEventListener(
        "click",
        () => {

            if (lastCalculation) {

                calculateFare(
                    lastCalculation
                );

            } else {

                resultCard.className =
                    "result-card";

            }

        }
    );

}


/* ============================================================
   CALCULATE FARE
============================================================ */

async function handleFareCalculation(
    event
) {

    event.preventDefault();


    const category =
        categorySelect.value;

    const energy =
        energySelect.value;

    const distance =
        Number(
            distanceInput.value
        );

    const seating =
        seatingSelect.value
            ? Number(
                seatingSelect.value
            )
            : null;

    const vehicleId =
        vehicleSelect.value
            ? Number(
                vehicleSelect.value
            )
            : null;


    if (!category) {

        showToast(
            "Please select a vehicle category."
        );

        return;
    }


    if (!energy) {

        showToast(
            "Please select the fuel or energy source."
        );

        return;
    }


    if (
        !Number.isFinite(distance) ||
        distance <= 0
    ) {

        showToast(
            "Please enter a valid journey distance."
        );

        distanceInput.focus();

        return;
    }


    const requestData = {

        category:
            category,

        energy_source:
            energy,

        distance_km:
            distance,

        seating_capacity:
            seating,

        vehicle_id:
            vehicleId

    };


    lastCalculation =
        requestData;


    await calculateFare(
        requestData
    );

}


/* ============================================================
   API FARE CALCULATION
============================================================ */

async function calculateFare(
    requestData
) {

    setCalculateLoading(
        true
    );


    try {

        const data =
            await apiFetch(
                "/api/fare/calculate",
                {
                    method: "POST",

                    body:
                        JSON.stringify(
                            requestData
                        )
                }
            );


        if (
            !data ||
            !data.success ||
            !data.calculation
        ) {

            throw new Error(
                "The API returned an invalid calculation."
            );
        }


        displayFareResult(
            data.calculation
        );


        showToast(
            "Fare calculated successfully."
        );


    } catch (error) {

        console.error(
            "Fare calculation error:",
            error
        );

        displayFareError(
            error.message
        );

    } finally {

        setCalculateLoading(
            false
        );

    }

}


/* ============================================================
   DISPLAY SUCCESS
============================================================ */

function displayFareResult(
    calculation
) {

    resultCard.className =
        "result-card show-success";


    const fare =
        Number(
            calculation.fare
        );


    fareAmount.textContent =
        Number.isFinite(fare)
            ? fare.toFixed(2)
            : "0.00";


    resultCategory.textContent =
        calculation.category ||
        "—";


    resultEnergy.textContent =
        calculation.energy_source ||
        "—";


    resultDistance.textContent =
        Number(
            calculation.distance_km
        ).toFixed(1);


    resultSeats.textContent =
        calculation.seating_capacity
            ? calculation.seating_capacity
            : "—";


    calculationMethod.textContent =
        formatCalculationMethod(
            calculation.calculation_method
        );


    if (
        calculation.fare_rule_id
    ) {

        fareRuleNote.textContent =
            `Applied fare rule #${calculation.fare_rule_id} from the connected fare database.`;

    } else {

        fareRuleNote.textContent =
            "Calculated using the system's fallback fare logic.";

    }


    /*
     * Smoothly bring result into view
     * on smaller screens.
     */

    if (
        window.innerWidth < 850
    ) {

        setTimeout(
            () => {

                resultCard.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });

            },
            100
        );

    }

}


/* ============================================================
   CALCULATION METHOD
============================================================ */

function formatCalculationMethod(
    method
) {

    if (!method) {

        return "Fare calculation";
    }


    const labels = {

        "database_fare_rule":
            "Database fare rule",

        "fallback_default":
            "Default fare calculation",

        "slab_calculation":
            "Fare slab calculation",

        "fuel_adjusted":
            "Fuel-adjusted calculation"

    };


    return (
        labels[method] ||
        method
            .replaceAll(
                "_",
                " "
            )
            .replace(
                /\b\w/g,
                char =>
                    char.toUpperCase()
            )
    );

}


/* ============================================================
   DISPLAY ERROR
============================================================ */

function displayFareError(
    message
) {

    resultCard.className =
        "result-card show-error";


    errorMessage.textContent =
        message ||
        "Unable to calculate the fare.";
}


/* ============================================================
   LOADING STATE
============================================================ */

function setCalculateLoading(
    loading
) {

    calculateBtn.disabled =
        loading;


    if (loading) {

        calculateBtn.classList.add(
            "loading"
        );

    } else {

        calculateBtn.classList.remove(
            "loading"
        );

    }

}


/* ============================================================
   RESET
============================================================ */

function resetCalculator() {

    fareForm.reset();

    resetDependentFields();

    resultCard.className =
        "result-card";

    lastCalculation =
        null;

    distanceInput.value =
        "";

    window.location.hash =
        "calculator";

}


function resetDependentFields() {

    vehicleSelect.innerHTML = `
        <option value="">
            Select vehicle model
        </option>
    `;

    seatingSelect.innerHTML = `
        <option value="">
            Select seats
        </option>
    `;

    vehicleGroup.style.display =
        "block";

    seatingGroup.style.display =
        "block";

}


/* ============================================================
   API STATUS
============================================================ */

async function checkAPIStatus() {

    try {

        const data =
            await apiFetch(
                "/api/health"
            );


        if (
            data.database_connected
        ) {

            footerStatus.textContent =
                "API & database online";

        } else if (
            data.database_configured
        ) {

            footerStatus.textContent =
                "API online";

        } else {

            footerStatus.textContent =
                "API online";
        }


    } catch {

        footerStatus.textContent =
            "API unavailable";
    }

}


/* ============================================================
   STATISTICS
============================================================ */

function updateStats() {

    categoryCount.textContent =
        categories.length ||
        "5";


    energyCount.textContent =
        energySources.length ||
        "5";


    vehicleCount.textContent =
        `${vehicles.length || 134}+`;


    vehicleCountStat.textContent =
        vehicles.length ||
        "134";

}


/* ============================================================
   TOAST
============================================================ */

let toastTimer = null;


function showToast(
    message
) {

    toastMessage.textContent =
        message;

    toast.classList.add(
        "show"
    );


    clearTimeout(
        toastTimer
    );


    toastTimer =
        setTimeout(
            () => {

                toast.classList.remove(
                    "show"
                );

            },
            3500
        );

}


/* ============================================================
   REVEAL ANIMATIONS
============================================================ */

function setupRevealAnimations() {

    const elements =
        document.querySelectorAll(
            ".stat-box, .process-card, .principle-card, .about-card, .calculator-card, .result-card"
        );


    elements.forEach(
        element => {

            element.classList.add(
                "reveal"
            );

        }
    );


    const observer =
        new IntersectionObserver(
            entries => {

                entries.forEach(
                    entry => {

                        if (
                            entry.isIntersecting
                        ) {

                            entry.target.classList.add(
                                "visible"
                            );

                            observer.unobserve(
                                entry.target
                            );

                        }

                    }
                );

            },
            {
                threshold: .12
            }
        );


    elements.forEach(
        element =>
            observer.observe(
                element
            )
    );

}


/* ============================================================
   INPUT POLISH
============================================================ */

distanceInput.addEventListener(
    "input",
    () => {

        if (
            Number(
                distanceInput.value
            ) > 1000
        ) {

            distanceInput.value =
                1000;

        }

    }
);


/* ============================================================
   KEYBOARD SHORTCUT
============================================================ */

document.addEventListener(
    "keydown",
    event => {

        /*
         * Press "/" to focus the calculator
         */

        if (
            event.key === "/" &&
            !["INPUT", "SELECT", "TEXTAREA"]
                .includes(
                    document.activeElement.tagName
                )
        ) {

            event.preventDefault();

            distanceInput.focus();

            document
                .getElementById(
                    "calculator"
                )
                .scrollIntoView({
                    behavior: "smooth"
                });

        }

    }
);