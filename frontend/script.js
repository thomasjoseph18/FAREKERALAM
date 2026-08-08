/* =========================================================
   FARE KERALAM
   Smart • Fair • Transparent
   Main JavaScript
========================================================= */

"use strict";


/* =========================================================
   1. PRELOADER
========================================================= */

window.addEventListener("load", () => {

    const preloader = document.getElementById("preloader");

    if (preloader) {
        setTimeout(() => {
            preloader.classList.add("hidden");
        }, 500);
    }

});


/* =========================================================
   2. NAVBAR
========================================================= */

const navbar = document.querySelector(".navbar");

window.addEventListener("scroll", () => {

    if (!navbar) return;

    if (window.scrollY > 50) {
        navbar.classList.add("scrolled");
    } else {
        navbar.classList.remove("scrolled");
    }

});


/* =========================================================
   3. MOBILE MENU
========================================================= */

const menuToggle = document.querySelector(".menu-toggle");
const navMenu = document.querySelector(".nav-menu");

if (menuToggle && navMenu) {

    menuToggle.addEventListener("click", () => {

        navMenu.classList.toggle("active");

        const icon = menuToggle.querySelector("i");

        if (icon) {

            if (navMenu.classList.contains("active")) {
                icon.classList.remove("fa-bars");
                icon.classList.add("fa-xmark");
            } else {
                icon.classList.remove("fa-xmark");
                icon.classList.add("fa-bars");
            }

        }

    });


    document.querySelectorAll(".nav-menu a").forEach(link => {

        link.addEventListener("click", () => {

            navMenu.classList.remove("active");

            const icon = menuToggle.querySelector("i");

            if (icon) {
                icon.classList.remove("fa-xmark");
                icon.classList.add("fa-bars");
            }

        });

    });

}


/* =========================================================
   4. SMOOTH SCROLL
========================================================= */

document.querySelectorAll('a[href^="#"]').forEach(anchor => {

    anchor.addEventListener("click", function (event) {

        const targetId = this.getAttribute("href");

        if (!targetId || targetId === "#") return;

        const target = document.querySelector(targetId);

        if (!target) return;

        event.preventDefault();

        target.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    });

});


/* =========================================================
   5. REVEAL ANIMATIONS
========================================================= */

const revealElements =
    document.querySelectorAll(
        ".reveal, .glass-card, .section-heading"
    );

const revealObserver =
    new IntersectionObserver(
        (entries, observer) => {

            entries.forEach(entry => {

                if (entry.isIntersecting) {

                    entry.target.classList.add("active");

                    observer.unobserve(entry.target);

                }

            });

        },
        {
            threshold: 0.12
        }
    );


revealElements.forEach(element => {

    element.classList.add("reveal");

    revealObserver.observe(element);

});


/* =========================================================
   6. FARE KERALAM FARE MODEL
=========================================================

   IMPORTANT:

   These are PROJECT PARAMETERS.

   They are NOT presented as current official
   Kerala Government rates.

   Once verified government notifications/data
   are connected, these values can be replaced
   automatically.
========================================================= */


/*
    General vehicle categories

    The important principle of Fare Keralam:

    Different fuel types should NOT automatically
    give the driver different profit margins.

    Instead:

        Fare = Operating Cost + Driver Margin

    Operating cost is calculated using:

        Fuel
        Maintenance
        Tyres
        Engine oil
        Depreciation
        Insurance / permits
        Other operating expenses

*/


const vehicleData = {

    auto: {

        name: "Auto Rickshaw",

        subtypes: {

            petrol: {
                fuel: "Petrol",
                mileage: 30,
                fuelPrice: 105
            },

            cng: {
                fuel: "CNG",
                mileage: 30,
                fuelPrice: 90
            },

            diesel: {
                fuel: "Diesel",
                mileage: 32,
                fuelPrice: 95
            }

        },

        minimumFare: 30,

        minimumDistance: 1.5,

        additionalRate: 15,

        additionalDistance: 1,

        driverMargin: 0.35

    },


    taxi: {

        name: "Taxi Car",

        subtypes: {

            petrol: {
                fuel: "Petrol",
                mileage: 14,
                fuelPrice: 105
            },

            diesel: {
                fuel: "Diesel",
                mileage: 18,
                fuelPrice: 95
            },

            cng: {
                fuel: "CNG",
                mileage: 22,
                fuelPrice: 90
            },

            electric: {
                fuel: "Electric",
                mileage: 7,
                fuelPrice: 9
            }

        },

        minimumFare: 200,

        minimumDistance: 4,

        additionalRate: 25,

        additionalDistance: 1,

        driverMargin: 0.35

    },


    sedan: {

        name: "Sedan",

        subtypes: {

            petrol: {
                fuel: "Petrol",
                mileage: 13,
                fuelPrice: 105
            },

            diesel: {
                fuel: "Diesel",
                mileage: 18,
                fuelPrice: 95
            },

            cng: {
                fuel: "CNG",
                mileage: 20,
                fuelPrice: 90
            },

            electric: {
                fuel: "Electric",
                mileage: 6.5,
                fuelPrice: 9
            }

        },

        minimumFare: 250,

        minimumDistance: 4,

        additionalRate: 28,

        additionalDistance: 1,

        driverMargin: 0.35

    },


    suv: {

        name: "SUV / MUV",

        subtypes: {

            petrol: {
                fuel: "Petrol",
                mileage: 9,
                fuelPrice: 105
            },

            diesel: {
                fuel: "Diesel",
                mileage: 13,
                fuelPrice: 95
            },

            cng: {
                fuel: "CNG",
                mileage: 15,
                fuelPrice: 90
            },

            electric: {
                fuel: "Electric",
                mileage: 5,
                fuelPrice: 9
            }

        },

        minimumFare: 300,

        minimumDistance: 4,

        additionalRate: 35,

        additionalDistance: 1,

        driverMargin: 0.35

    },


    traveller: {

        name: "Traveller / Van",

        subtypes: {

            diesel: {
                fuel: "Diesel",
                mileage: 11,
                fuelPrice: 95
            },

            petrol: {
                fuel: "Petrol",
                mileage: 8,
                fuelPrice: 105
            },

            electric: {
                fuel: "Electric",
                mileage: 5,
                fuelPrice: 9
            }

        },

        minimumFare: 500,

        minimumDistance: 5,

        additionalRate: 50,

        additionalDistance: 1,

        driverMargin: 0.30

    },


    bus: {

        name: "Route Bus",

        subtypes: {

            diesel: {
                fuel: "Diesel",
                mileage: 4,
                fuelPrice: 95
            },

            electric: {
                fuel: "Electric",
                mileage: 1.8,
                fuelPrice: 9
            }

        },

        minimumFare: 10,

        minimumDistance: 1,

        additionalRate: 2,

        additionalDistance: 1,

        driverMargin: 0.20

    },


    touristBus: {

        name: "Tourist Bus",

        subtypes: {

            diesel: {
                fuel: "Diesel",
                mileage: 4,
                fuelPrice: 95
            },

            electric: {
                fuel: "Electric",
                mileage: 1.8,
                fuelPrice: 9
            }

        },

        minimumFare: 1500,

        minimumDistance: 10,

        additionalRate: 100,

        additionalDistance: 1,

        driverMargin: 0.25

    }

};


/* =========================================================
   7. FUEL PRICE INDEX
========================================================= */

const fuelPrices = {

    petrol: 105,

    diesel: 95,

    cng: 90,

    electric: 9

};


/* =========================================================
   8. DOM ELEMENTS
========================================================= */

const vehicleType =
    document.getElementById("vehicleType");

const vehicleSubtype =
    document.getElementById("vehicleSubtype");

const distanceInput =
    document.getElementById("distance");

const fareResult =
    document.getElementById("fareResult");

const fareVehicle =
    document.getElementById("fareVehicle");

const fareFuel =
    document.getElementById("fareFuel");

const fareDistance =
    document.getElementById("fareDistance");

const fuelCost =
    document.getElementById("fuelCost");

const operatingCost =
    document.getElementById("operatingCost");

const driverProfit =
    document.getElementById("driverProfit");

const fareTotal =
    document.getElementById("fareTotal");

const calculateButton =
    document.getElementById("calculateFare");


/* =========================================================
   9. UPDATE SUBTYPE DROPDOWN
========================================================= */

function updateVehicleSubtypes() {

    if (!vehicleType || !vehicleSubtype) return;

    const type =
        vehicleType.value;

    vehicleSubtype.innerHTML =
        `<option value="">Select fuel / power</option>`;

    if (!type || !vehicleData[type]) {

        vehicleSubtype.disabled = true;

        return;
    }

    const subtypes =
        vehicleData[type].subtypes;

    Object.keys(subtypes).forEach(key => {

        const data =
            subtypes[key];

        const option =
            document.createElement("option");

        option.value = key;

        option.textContent =
            data.fuel;

        vehicleSubtype.appendChild(option);

    });

    vehicleSubtype.disabled = false;

}


if (vehicleType) {

    vehicleType.addEventListener(
        "change",
        updateVehicleSubtypes
    );

}


/* =========================================================
   10. FUEL PRICE UPDATE
========================================================= */

function getCurrentFuelPrice(fuel) {

    return fuelPrices[fuel] || 0;

}


/* =========================================================
   11. OPERATING COST CALCULATION
========================================================= */

function calculateOperatingCost(
    distance,
    vehicle,
    subtype
) {

    const data =
        vehicleData[vehicle].subtypes[subtype];

    if (!data) return 0;

    const fuelPrice =
        getCurrentFuelPrice(subtype);

    const mileage =
        data.mileage;

    /*
        Fuel consumption
    */

    const fuelUsed =
        distance / mileage;

    const fuelExpense =
        fuelUsed * fuelPrice;


    /*
        Maintenance factor

        This represents:

        tyres
        engine oil
        servicing
        wear & tear
    */

    let maintenanceRate;

    switch (vehicle) {

        case "auto":
            maintenanceRate = 2.2;
            break;

        case "taxi":
            maintenanceRate = 3.0;
            break;

        case "sedan":
            maintenanceRate = 3.5;
            break;

        case "suv":
            maintenanceRate = 5.0;
            break;

        case "traveller":
            maintenanceRate = 6.5;
            break;

        case "bus":
            maintenanceRate = 8.0;
            break;

        case "touristBus":
            maintenanceRate = 10.0;
            break;

        default:
            maintenanceRate = 3;
    }


    const maintenanceCost =
        distance * maintenanceRate;


    return {

        fuelUsed,

        fuelExpense,

        maintenanceCost,

        totalOperatingCost:
            fuelExpense +
            maintenanceCost

    };

}


/* =========================================================
   12. SLAB CALCULATION
========================================================= */

function calculateSlabFare(
    distance,
    vehicle,
    subtype
) {

    const data =
        vehicleData[vehicle];

    if (!data) return null;

    /*
        Minimum distance slab
    */

    if (
        distance <=
        data.minimumDistance
    ) {

        return {

            fare:
                data.minimumFare,

            slab:
                `Up to ${data.minimumDistance} km`,

            extraDistance: 0

        };

    }


    /*
        Distance beyond minimum slab
    */

    const extraDistance =
        distance -
        data.minimumDistance;


    const additionalUnits =
        Math.ceil(
            extraDistance /
            data.additionalDistance
        );


    const additionalFare =
        additionalUnits *
        data.additionalRate;


    const fare =
        data.minimumFare +
        additionalFare;


    return {

        fare,

        slab:
            `Above ${data.minimumDistance} km`,

        extraDistance,

        additionalUnits,

        additionalFare

    };

}


/* =========================================================
   13. CALCULATE FARE
========================================================= */

function calculateFare() {

    if (
        !vehicleType ||
        !vehicleSubtype ||
        !distanceInput
    ) return;


    const vehicle =
        vehicleType.value;

    const subtype =
        vehicleSubtype.value;

    const distance =
        parseFloat(
            distanceInput.value
        );


    if (!vehicle) {

        showMessage(
            "Please select a vehicle type."
        );

        return;

    }


    if (!subtype) {

        showMessage(
            "Please select the fuel / power type."
        );

        return;

    }


    if (
        !distance ||
        distance <= 0
    ) {

        showMessage(
            "Please enter a valid distance."
        );

        return;

    }


    const operating =
        calculateOperatingCost(
            distance,
            vehicle,
            subtype
        );


    const slab =
        calculateSlabFare(
            distance,
            vehicle,
            subtype
        );


    if (!operating || !slab) return;


    /*
        The displayed fare follows
        the current slab model.

        The operating cost is shown
        separately for transparency.
    */

    const totalFare =
        slab.fare;


    const profit =
        Math.max(
            0,
            totalFare -
            operating.totalOperatingCost
        );


    updateFareUI({

        vehicle,
        subtype,
        distance,

        operating,

        slab,

        totalFare,

        profit

    });

}


/* =========================================================
   14. UPDATE RESULT UI
========================================================= */

function updateFareUI(result) {

    const {
        vehicle,
        subtype,
        distance,
        operating,
        slab,
        totalFare,
        profit
    } = result;


    if (fareResult) {

        fareResult.textContent =
            `₹${Math.round(totalFare)}`;

    }


    if (fareVehicle) {

        fareVehicle.textContent =
            vehicleData[vehicle].name;

    }


    if (fareFuel) {

        fareFuel.textContent =
            vehicleData[vehicle]
                .subtypes[subtype]
                .fuel;

    }


    if (fareDistance) {

        fareDistance.textContent =
            `${distance.toFixed(1)} km`;

    }


    if (fuelCost) {

        fuelCost.textContent =
            `₹${Math.round(
                operating.fuelExpense
            )}`;

    }


    if (operatingCost) {

        operatingCost.textContent =
            `₹${Math.round(
                operating.totalOperatingCost
            )}`;

    }


    if (driverProfit) {

        driverProfit.textContent =
            `₹${Math.round(profit)}`;

    }


    if (fareTotal) {

        fareTotal.textContent =
            `₹${Math.round(totalFare)}`;

    }


    /*
        Update slab progress
    */

    updateSlabProgress(
        distance,
        vehicle
    );


    /*
        Update result status
    */

    const resultStatus =
        document.querySelector(
            ".result-status"
        );

    if (resultStatus) {

        resultStatus.textContent =
            "CALCULATED";

    }

}


/* =========================================================
   15. SLAB PROGRESS
========================================================= */

function updateSlabProgress(
    distance,
    vehicle
) {

    const data =
        vehicleData[vehicle];

    if (!data) return;

    const progress =
        document.querySelector(
            ".slab-progress-fill"
        );

    if (!progress) return;


    /*
        Visual representation only.
    */

    const percentage =
        Math.min(
            100,
            (
                distance /
                Math.max(
                    data.minimumDistance * 5,
                    20
                )
            ) * 100
        );


    progress.style.width =
        `${percentage}%`;


    const activeSlab =
        document.querySelector(
            ".slab-active"
        );

    if (activeSlab) {

        if (
            distance <=
            data.minimumDistance
        ) {

            activeSlab.textContent =
                "Minimum fare slab";

        } else {

            activeSlab.textContent =
                `₹${data.additionalRate}/additional unit`;

        }

    }

}


/* =========================================================
   16. CALCULATE BUTTON
========================================================= */

if (calculateButton) {

    calculateButton.addEventListener(
        "click",
        calculateFare
    );

}


/* =========================================================
   17. ENTER KEY CALCULATION
========================================================= */

if (distanceInput) {

    distanceInput.addEventListener(
        "keydown",
        event => {

            if (
                event.key ===
                "Enter"
            ) {

                calculateFare();

            }

        }
    );

}


/* =========================================================
   18. USER MESSAGE
========================================================= */

function showMessage(message) {

    /*
        Use existing result card
        rather than browser alert.
    */

    if (fareResult) {

        fareResult.textContent =
            "—";

    }

    const messageElement =
        document.querySelector(
            ".fare-note p"
        );

    if (messageElement) {

        messageElement.textContent =
            message;

    }

}


/* =========================================================
   19. FUEL PRICE INDEX
=========================================================

   General formula:

       Fuel Index =
       Current Fuel Cost /
       Reference Fuel Cost

   The system does NOT need to
   change the fare every day.

   Instead the index can be used
   to determine when a new slab
   should be triggered.
========================================================= */

function calculateFuelIndex(
    fuel,
    referencePrice
) {

    const currentPrice =
        getCurrentFuelPrice(fuel);

    if (!referencePrice) return 1;

    return (
        currentPrice /
        referencePrice
    );

}


/* =========================================================
   20. OPERATING COST INDEX
========================================================= */

function calculateOperatingCostIndex(
    vehicle,
    subtype,
    referencePrice
) {

    const data =
        vehicleData[vehicle]
            ?.subtypes[subtype];

    if (!data) return 1;


    const currentPrice =
        getCurrentFuelPrice(subtype);


    const currentFuelCostPerKm =
        currentPrice /
        data.mileage;


    const referenceFuelCostPerKm =
        referencePrice /
        data.mileage;


    return (
        currentFuelCostPerKm /
        referenceFuelCostPerKm
    );

}


/* =========================================================
   21. SLAB TRIGGER LOGIC
=========================================================

   Example:

   Fuel price does NOT immediately
   change the fare.

   The system waits until the
   calculated operating-cost index
   crosses a predefined threshold.

========================================================= */

const slabPolicy = {

    reviewThreshold: 0.10,

    /*
        10% operating-cost change
        triggers a fare review.

        This is a project policy,
        not an official government rule.
    */

    implementationThreshold: 0.15

};


function shouldReviewFare(
    currentIndex
) {

    return (
        Math.abs(
            currentIndex - 1
        ) >=
        slabPolicy.reviewThreshold
    );

}


/* =========================================================
   22. FAIRNESS CHECK
========================================================= */

function calculateFairness(
    fare,
    operatingCost
) {

    if (
        !fare ||
        fare <= 0
    ) {

        return 0;

    }


    return (
        (fare - operatingCost) /
        fare
    ) * 100;

}


/* =========================================================
   23. LIVE FUEL PRICE DISPLAY
========================================================= */

function updateFuelPriceDisplay() {

    const fuelElements =
        document.querySelectorAll(
            "[data-fuel-price]"
        );


    fuelElements.forEach(element => {

        const fuel =
            element.dataset.fuelPrice;

        const price =
            getCurrentFuelPrice(fuel);

        element.textContent =
            `₹${price.toFixed(2)}`;

    });

}


updateFuelPriceDisplay();


/* =========================================================
   24. FUEL PRICE DATA UPDATE
=========================================================

   Later this function can be connected
   to verified government / official
   fuel-price sources.

   Example:

       updateFuelPrice("petrol", 104.90)

========================================================= */

function updateFuelPrice(
    fuel,
    price
) {

    if (
        !fuel ||
        typeof price !== "number" ||
        price <= 0
    ) return;


    fuelPrices[fuel] =
        price;


    /*
        Update vehicle database
    */

    Object.keys(vehicleData)
        .forEach(vehicle => {

            const subtypes =
                vehicleData[vehicle]
                    .subtypes;

            if (subtypes[fuel]) {

                subtypes[fuel]
                    .fuelPrice =
                    price;

            }

        });


    updateFuelPriceDisplay();

}


/* =========================================================
   25. CHART.JS — FARE / FUEL ANALYSIS
========================================================= */

const chartCanvas =
    document.getElementById(
        "fareCostChart"
    );


let fareCostChart = null;


function createFareChart() {

    if (!chartCanvas) return;

    /*
        Chart.js is expected to be
        loaded in index.html.
    */

    if (
        typeof Chart ===
        "undefined"
    ) {

        console.warn(
            "Chart.js is not loaded."
        );

        return;

    }


    const ctx =
        chartCanvas.getContext(
            "2d"
        );


    fareCostChart =
        new Chart(
            ctx,
            {

                type: "line",

                data: {

                    labels: [
                        "2017",
                        "2018",
                        "2019",
                        "2020",
                        "2021",
                        "2022",
                        "2023",
                        "2024",
                        "2025",
                        "2026"
                    ],

                    datasets: [

                        {

                            label:
                                "Fuel Cost Index",

                            data: [
                                100,
                                104,
                                108,
                                105,
                                115,
                                128,
                                132,
                                137,
                                141,
                                145
                            ],

                            tension: .35,

                            fill: false

                        },

                        {

                            label:
                                "Fare Index",

                            data: [
                                100,
                                100,
                                104,
                                104,
                                110,
                                118,
                                122,
                                128,
                                132,
                                135
                            ],

                            tension: .35,

                            fill: false

                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    interaction: {

                        mode: "index",

                        intersect: false

                    },

                    plugins: {

                        legend: {

                            labels: {

                                color:
                                    "#b8c0d9",

                                font: {

                                    size: 10

                                }

                            }

                        }

                    },

                    scales: {

                        x: {

                            ticks: {

                                color:
                                    "#78829e",

                                font: {

                                    size: 9

                                }

                            },

                            grid: {

                                color:
                                    "rgba(255,255,255,.04)"

                            }

                        },

                        y: {

                            ticks: {

                                color:
                                    "#78829e",

                                font: {

                                    size: 9

                                }

                            },

                            grid: {

                                color:
                                    "rgba(255,255,255,.04)"

                            }

                        }

                    }

                }

            }
        );

}


createFareChart();


/* =========================================================
   26. CHART FILTER
========================================================= */

const chartFilter =
    document.getElementById(
        "chartFilter"
    );


if (chartFilter) {

    chartFilter.addEventListener(
        "change",
        () => {

            if (!fareCostChart) return;


            const value =
                chartFilter.value;


            if (
                value === "fuel"
            ) {

                fareCostChart.data.datasets =
                    [

                        {

                            label:
                                "Fuel Cost Index",

                            data: [
                                100,
                                104,
                                108,
                                105,
                                115,
                                128,
                                132,
                                137,
                                141,
                                145
                            ],

                            tension: .35,

                            fill: false

                        }

                    ];

            }


            else if (
                value === "fare"
            ) {

                fareCostChart.data.datasets =
                    [

                        {

                            label:
                                "Fare Index",

                            data: [
                                100,
                                100,
                                104,
                                104,
                                110,
                                118,
                                122,
                                128,
                                132,
                                135
                            ],

                            tension: .35,

                            fill: false

                        }

                    ];

            }


            else {

                fareCostChart.data.datasets =
                    [

                        {

                            label:
                                "Fuel Cost Index",

                            data: [
                                100,
                                104,
                                108,
                                105,
                                115,
                                128,
                                132,
                                137,
                                141,
                                145
                            ],

                            tension: .35,

                            fill: false

                        },

                        {

                            label:
                                "Fare Index",

                            data: [
                                100,
                                100,
                                104,
                                104,
                                110,
                                118,
                                122,
                                128,
                                132,
                                135
                            ],

                            tension: .35,

                            fill: false

                        }

                    ];

            }


            fareCostChart.update();

        }
    );

}


/* =========================================================
   27. BACK TO TOP
========================================================= */

const backToTop =
    document.querySelector(
        ".back-to-top"
    );


window.addEventListener(
    "scroll",
    () => {

        if (!backToTop) return;

        if (window.scrollY > 500) {

            backToTop.classList.add(
                "visible"
            );

        } else {

            backToTop.classList.remove(
                "visible"
            );

        }

    }
);


if (backToTop) {

    backToTop.addEventListener(
        "click",
        () => {

            window.scrollTo({

                top: 0,

                behavior: "smooth"

            });

        }
    );

}


/* =========================================================
   28. VEHICLE CATEGORY INFORMATION
========================================================= */

function getVehicleInformation(
    vehicle
) {

    return vehicleData[vehicle] || null;

}


/* =========================================================
   29. EXAMPLE API-READY FUEL UPDATE
=========================================================

   When the backend is ready:

   fetch("/api/fuel-prices")
       .then(response => response.json())
       .then(data => {
           updateFuelPrice(
               "petrol",
               data.petrol
           );
       });

========================================================= */


/* =========================================================
   30. API-READY OPERATING COST MODEL
========================================================= */

function calculateDetailedOperatingCost(
    distance,
    vehicle,
    subtype,
    costs = {}
) {

    const data =
        vehicleData[vehicle]
            ?.subtypes[subtype];

    if (!data) return null;


    const fuelPrice =
        costs.fuelPrice ??
        getCurrentFuelPrice(subtype);


    const tyreCostPerKm =
        costs.tyreCostPerKm ??
        0;


    const engineOilCostPerKm =
        costs.engineOilCostPerKm ??
        0;


    const serviceCostPerKm =
        costs.serviceCostPerKm ??
        0;


    const insuranceCostPerKm =
        costs.insuranceCostPerKm ??
        0;


    const depreciationCostPerKm =
        costs.depreciationCostPerKm ??
        0;


    const fuelCostPerKm =
        fuelPrice /
        data.mileage;


    const totalCostPerKm =
        fuelCostPerKm +
        tyreCostPerKm +
        engineOilCostPerKm +
        serviceCostPerKm +
        insuranceCostPerKm +
        depreciationCostPerKm;


    const totalCost =
        totalCostPerKm *
        distance;


    return {

        fuelCostPerKm,

        tyreCostPerKm,

        engineOilCostPerKm,

        serviceCostPerKm,

        insuranceCostPerKm,

        depreciationCostPerKm,

        totalCostPerKm,

        totalCost

    };

}


/* =========================================================
   31. FAIR DRIVER PROFIT MODEL
========================================================= */

function calculateDriverProfit(
    fare,
    operatingCost
) {

    if (
        typeof fare !== "number" ||
        typeof operatingCost !== "number"
    ) {

        return null;

    }


    return Math.max(
        0,
        fare - operatingCost
    );

}


/* =========================================================
   32. GENERAL FARE FORMULA
=========================================================

   Fare Keralam concept:

       Operating Cost
       +
       Fair Driver Margin
       =
       Sustainable Fare

   Fuel type should affect operating
   cost, but the intended driver
   margin should remain comparable.

========================================================= */

function calculateFairFare(
    operatingCost,
    marginPercentage
) {

    if (
        operatingCost <= 0
    ) {

        return 0;

    }


    return (
        operatingCost /
        (1 - marginPercentage)
    );

}


/* =========================================================
   33. FARE ROUNDING
========================================================= */

function roundFare(
    amount,
    nearest = 5
) {

    return (
        Math.ceil(
            amount /
            nearest
        ) * nearest
    );

}


/* =========================================================
   34. FINAL PROJECT OBJECT
========================================================= */

const FareKeralam = {

    version: "1.0",

    vehicleData,

    fuelPrices,

    calculateFare,

    calculateSlabFare,

    calculateOperatingCost,

    calculateDetailedOperatingCost,

    calculateFairFare,

    calculateDriverProfit,

    calculateFuelIndex,

    calculateOperatingCostIndex,

    shouldReviewFare,

    roundFare,

    updateFuelPrice,

    getVehicleInformation

};


/* =========================================================
   35. GLOBAL ACCESS
========================================================= */

window.FareKeralam =
    FareKeralam;


/* =========================================================
   36. INITIALISE
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        updateVehicleSubtypes();

        updateFuelPriceDisplay();

        console.log(
            "Fare Keralam initialized successfully."
        );

    }
);