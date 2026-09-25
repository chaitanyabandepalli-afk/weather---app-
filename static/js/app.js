// Weather Forecast Analysis — Frontend Controller
// No calculations here — everything comes from the Flask backend.

let currentAnalysisData = null;
let currentCity = { name: "Hyderabad", lat: 17.3850, lon: 78.4867 };
let charts = {};   // chart.js instances
let isLoading = false;

// ─────────────────────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    setupTabNavigation();
    setupCitySelection();
    setupEventListeners();
    loadVivaGuide();

    // Auto-load Hyderabad 5-year analysis on page open
    triggerAnalysis();
});


// ─────────────────────────────────────────────────────────────
// TAB NAVIGATION
// ─────────────────────────────────────────────────────────────
function setupTabNavigation() {
    const btns  = document.querySelectorAll(".tab-btn");
    const panes = document.querySelectorAll(".tab-pane");

    btns.forEach(btn => {
        btn.addEventListener("click", () => {
            btns.forEach(b => b.classList.remove("active"));
            panes.forEach(p => p.classList.remove("active"));
            btn.classList.add("active");
            const pane = document.getElementById(btn.dataset.tab);
            if (pane) pane.classList.add("active");

            renderMath();
        });
    });
}

function renderMath() {
    if (window.renderMathInElement) {
        renderMathInElement(document.body, {
            delimiters: [
                { left: '$$', right: '$$', display: true },
                { left: '$',  right: '$',  display: false },
            ]
        });
    }
}


// ─────────────────────────────────────────────────────────────
// CITY SELECTION & GEOCODING
// ─────────────────────────────────────────────────────────────
function updateActiveChip(cityName) {
    const chips = document.querySelectorAll(".quick-chip");
    chips.forEach(chip => {
        if (chip.dataset.city && chip.dataset.city.toLowerCase() === (cityName || "").toLowerCase()) {
            chip.classList.add("active");
        } else {
            chip.classList.remove("active");
        }
    });
}

function setupCitySelection() {
    const input   = document.getElementById("cityInput");
    const search  = document.getElementById("searchBtn");
    const suggest = document.getElementById("citySuggestions");
    const chips   = document.querySelectorAll(".quick-chip");

    // Quick-pick chips
    chips.forEach(chip => {
        chip.addEventListener("click", () => {
            chips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            input.value = chip.dataset.city;
            currentCity = {
                name: chip.dataset.city,
                lat: parseFloat(chip.dataset.lat),
                lon: parseFloat(chip.dataset.lon),
            };
            triggerAnalysis();
        });
    });

    // Live search with debounce
    let timer;
    input.addEventListener("input", () => {
        clearTimeout(timer);
        const q = input.value.trim();
        if (q.length < 2) { suggest.style.display = "none"; return; }
        timer = setTimeout(() => searchCity(q, suggest, input), 300);
    });

    search.addEventListener("click", () => {
        const q = input.value.trim();
        if (q.length >= 2) searchCity(q, suggest, input, true);
    });

    // Enter key triggers search & immediate analysis
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            const q = input.value.trim();
            if (q.length >= 2) searchCity(q, suggest, input, true);
        }
    });

    document.addEventListener("click", (e) => {
        if (!input.contains(e.target) && !suggest.contains(e.target))
            suggest.style.display = "none";
    });
}

function searchCity(query, suggestBox, input, autoSelect) {
    fetch(`/api/cities?query=${encodeURIComponent(query)}`)
        .then(r => r.json())
        .then(data => {
            if (data.status !== "success" || !data.cities.length) {
                suggestBox.style.display = "none";
                return;
            }
            if (autoSelect) {
                const c = data.cities[0];
                input.value = c.name;
                currentCity = { name: c.name, lat: c.lat, lon: c.lon };
                updateActiveChip(c.name);
                suggestBox.style.display = "none";
                triggerAnalysis();
                return;
            }
            suggestBox.innerHTML = "";
            data.cities.forEach(c => {
                const div = document.createElement("div");
                div.className = "city-item";
                div.textContent = `${c.name}, ${c.country}`;
                div.addEventListener("click", () => {
                    input.value = c.name;
                    currentCity = { name: c.name, lat: c.lat, lon: c.lon };
                    updateActiveChip(c.name);
                    suggestBox.style.display = "none";
                    triggerAnalysis();
                });
                suggestBox.appendChild(div);
            });
            suggestBox.style.display = "block";
        })
        .catch(() => { suggestBox.style.display = "none"; });
}


// ─────────────────────────────────────────────────────────────
// EVENT LISTENERS
// ─────────────────────────────────────────────────────────────
function setupEventListeners() {
    // When Analyze button is clicked, check if user changed city in input
    document.getElementById("analyzeBtn").addEventListener("click", () => {
        const inputVal = document.getElementById("cityInput").value.trim();
        if (inputVal && inputVal.toLowerCase() !== currentCity.name.toLowerCase()) {
            const suggest = document.getElementById("citySuggestions");
            searchCity(inputVal, suggest, document.getElementById("cityInput"), true);
        } else {
            triggerAnalysis();
        }
    });

    document.getElementById("futureYearSlider").addEventListener("input", (e) => {
        const yr = parseInt(e.target.value);
        document.getElementById("sliderValDisplay").textContent = yr;
        updatePredictionCards(yr);
    });

    document.getElementById("exportCsvBtn").addEventListener("click", exportCSV);
}


// ─────────────────────────────────────────────────────────────
// TRIGGER ANALYSIS  (called on every city/range change)
// ─────────────────────────────────────────────────────────────
function triggerAnalysis() {
    if (isLoading) return;

    const range    = parseInt(document.getElementById("yearRangeSelect").value);
    const endYear  = new Date().getFullYear() - 1;   // last complete year
    const startYear = endYear - range + 1;

    const btn = document.getElementById("analyzeBtn");
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';
    isLoading = true;

    const badge = document.getElementById("apiStatusText");
    badge.textContent = `Fetching ${currentCity.name} data (${startYear}–${endYear})…`;

    fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            city:       currentCity.name,
            lat:        currentCity.lat,
            lon:        currentCity.lon,
            start_year: startYear,
            end_year:   endYear,
        }),
    })
    .then(r => r.json())
    .then(data => {
        isLoading = false;
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-chart-line"></i> Analyze & Predict';

        if (data.status === "success") {
            currentAnalysisData = data;
            // Sync city name & coordinates if normalized/resolved by backend
            if (data.metadata && data.metadata.city) {
                currentCity.name = data.metadata.city;
                currentCity.lat  = data.metadata.latitude;
                currentCity.lon  = data.metadata.longitude;
                document.getElementById("cityInput").value = data.metadata.city;
                updateActiveChip(data.metadata.city);
            }
            badge.textContent = data.metadata.data_source;
            renderDashboard(data);
        } else {
            badge.textContent = "Error — check console";
        }
    })
    .catch(err => {
        console.error("Fetch error:", err);
        isLoading = false;
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-chart-line"></i> Analyze & Predict';
        badge.textContent = "Connection error";
    });
}


// ─────────────────────────────────────────────────────────────
// RENDER FULL DASHBOARD
// ─────────────────────────────────────────────────────────────
function renderDashboard(d) {
    const ts = d.descriptive_stats.temperature;
    const pa = d.probability_analysis;
    const fp = d.future_predictions[0];

    // KPI cards
    setText("kpiMeanTemp",    `${ts.mean} °C`);
    setText("kpiMeanTempSub", ts.steps.mean);
    setText("kpiStdDev",      `±${ts.std_dev} °C`);
    setText("kpiStdDevSub",   ts.steps.std_dev);
    setText("kpiRainProb",    `${pa.rain_percentage} %`);
    setText("kpiRainProbSub", pa.prob_step);

    const avgRain = (d.yearly_summary.reduce((a, y) => a + y.total_precip, 0)
                     / d.yearly_summary.length).toFixed(1);
    setText("kpiRainSum",    `${avgRain} mm`);
    setText("kpiRainSumSub", `Average annual precipitation over ${d.yearly_summary.length} years`);

    setText("kpiForecast2026",  `${fp.predicted_avg_temp} °C`);
    setText("kpiForecastSub",   fp.step);
    setText("overviewCityBadge", `${d.metadata.city} (${d.metadata.start_year}–${d.metadata.end_year})`);

    // Update future year slider range
    const slider = document.getElementById("futureYearSlider");
    const firstFuture = d.future_predictions[0].year;
    const lastFuture  = d.future_predictions[d.future_predictions.length - 1].year;
    slider.min = firstFuture;
    slider.max = lastFuture;
    slider.value = firstFuture;
    setText("sliderValDisplay", firstFuture);

    renderOverview(d);
    renderStats(d);
    renderRainfall(d);
    renderNormalDist(d);
    renderTimeSeries(d);
    renderPrediction(d);
    renderRawData(d);
    renderMath();
}


// ─────────────────────────────────────────────────────────────
// OVERVIEW TAB
// ─────────────────────────────────────────────────────────────
function renderOverview(d) {
    // Trend chart (sampled every 5th day for performance)
    destroyChart("overviewTrend");
    const step = 5;
    const dates = d.time_series.dates.filter((_, i) => i % step === 0);
    const temps = d.time_series.temps.filter((_, i) => i % step === 0);
    const ma30  = d.time_series.moving_avg_30.filter((_, i) => i % step === 0);

    charts.overviewTrend = new Chart(getCtx("overviewTrendChart"), {
        type: "line",
        data: {
            labels: dates,
            datasets: [
                { label: "Daily Mean Temp (°C)", data: temps, borderColor: "rgba(0,242,254,0.35)", borderWidth: 1, pointRadius: 0, tension: 0.1 },
                { label: "30-Day Moving Avg",    data: ma30,  borderColor: "#00f2fe", borderWidth: 2.5, pointRadius: 0, tension: 0.3 },
            ]
        },
        options: chartOpts("Temperature (°C)")
    });

    // Doughnut (rainy vs dry)
    destroyChart("overviewDoughnut");
    charts.overviewDoughnut = new Chart(getCtx("overviewDoughnutChart"), {
        type: "doughnut",
        data: {
            labels: ["Dry Days", "Rainy Days"],
            datasets: [{
                data: [d.probability_analysis.total_dry_days, d.probability_analysis.total_rainy_days],
                backgroundColor: ["rgba(255,255,255,0.1)", "#4facfe"],
                borderColor: ["rgba(255,255,255,0.2)", "#00f2fe"],
                borderWidth: 1,
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: "#94a3b8" } } } }
    });

    // Yearly table
    const tb = document.querySelector("#yearlySummaryTable tbody");
    tb.innerHTML = "";
    d.yearly_summary.forEach(y => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${y.year}</strong></td>
            <td>${y.avg_temp} °C</td>
            <td>${y.max_temp} °C</td>
            <td>${y.min_temp} °C</td>
            <td>${y.total_precip} mm</td>
            <td>${y.rainy_days} / ${y.total_days}</td>
            <td><span class="badge blue">${(y.rain_probability * 100).toFixed(1)}%</span></td>`;
        tb.appendChild(tr);
    });
}


// ─────────────────────────────────────────────────────────────
// DESCRIPTIVE STATS TAB
// ─────────────────────────────────────────────────────────────
function renderStats(d) {
    const t = d.descriptive_stats.temperature;

    setText("statMeanVal",     `${t.mean} °C`);
    setText("statMedianVal",   `${t.median} °C`);
    setText("statModeVal",     `${t.mode} °C`);
    setText("statVarianceVal", `${t.variance}`);
    setText("statStdVal",      `${t.std_dev} °C`);
    setText("statRangeVal",    `${t.range} °C (IQR: ${t.iqr}°C)`);

    // Step-by-step calculations display
    const stepsBox = document.getElementById("calcStepsBox");
    if (stepsBox && t.steps) {
        stepsBox.innerHTML = "";
        const entries = [
            { title: "Mean Calculation",     detail: t.steps.mean },
            { title: "Median Calculation",   detail: t.steps.median },
            { title: "Mode Calculation",     detail: t.steps.mode },
            { title: "Variance Calculation", detail: t.steps.variance },
            { title: "Std Dev Calculation",  detail: t.steps.std_dev },
            { title: "Range & IQR",          detail: `${t.steps.range}\n${t.steps.iqr}` },
        ];
        entries.forEach(e => {
            const div = document.createElement("div");
            div.className = "calc-step-item";
            div.innerHTML = `<strong>${e.title}:</strong> <span>${e.detail}</span>`;
            stepsBox.appendChild(div);
        });
    }

    // Full multi-variable table
    const tb = document.querySelector("#fullStatsTable tbody");
    tb.innerHTML = "";
    [
        { name: "Temperature (°C)",    s: d.descriptive_stats.temperature },
        { name: "Precipitation (mm)",  s: d.descriptive_stats.precipitation },
        { name: "Humidity (%)",        s: d.descriptive_stats.humidity },
        { name: "Wind Speed (km/h)",   s: d.descriptive_stats.wind_speed },
    ].forEach(v => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${v.name}</strong></td>
            <td>${v.s.n}</td>
            <td><strong>${v.s.mean}</strong></td>
            <td>${v.s.median}</td>
            <td>${v.s.mode}</td>
            <td>${v.s.variance}</td>
            <td><strong>${v.s.std_dev}</strong></td>
            <td>${v.s.min}</td>
            <td>${v.s.max}</td>
            <td>${v.s.iqr}</td>`;
        tb.appendChild(tr);
    });
}


// ─────────────────────────────────────────────────────────────
// RAINFALL PROBABILITY TAB
// ─────────────────────────────────────────────────────────────
function renderRainfall(d) {
    const ms = d.monthly_summary;

    // Bar + Line combo chart
    destroyChart("monthlyRain");
    charts.monthlyRain = new Chart(getCtx("monthlyRainChart"), {
        type: "bar",
        data: {
            labels: ms.map(m => m.month_name),
            datasets: [
                { type: "bar",  label: "Total Rainfall (mm)", data: ms.map(m => m.total_precip),   backgroundColor: "rgba(79,172,254,0.4)", borderColor: "#4facfe", borderWidth: 1.5, yAxisID: "y" },
                { type: "line", label: "Rain Probability (%)", data: ms.map(m => m.rain_percentage), borderColor: "#00f2fe", borderWidth: 2.5, pointBackgroundColor: "#00f2fe", yAxisID: "y1" },
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: {
                x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
                y:  { position: "left",  title: { display: true, text: "Rainfall (mm)", color: "#94a3b8" }, ticks: { color: "#94a3b8" } },
                y1: { position: "right", title: { display: true, text: "Probability (%)", color: "#94a3b8" }, ticks: { color: "#94a3b8" }, grid: { drawOnChartArea: false } },
            },
            plugins: { legend: { labels: { color: "#94a3b8" } } }
        }
    });

    // Intensity doughnut
    destroyChart("rainIntensity");
    const ic = d.probability_analysis.intensity_counts;
    charts.rainIntensity = new Chart(getCtx("rainIntensityChart"), {
        type: "doughnut",
        data: {
            labels: ["Dry (0mm)", "Light (0.5–5mm)", "Moderate (5–20mm)", "Heavy (>20mm)"],
            datasets: [{
                data: [ic.dry, ic.light, ic.moderate, ic.heavy],
                backgroundColor: ["rgba(255,255,255,0.1)", "#4facfe", "#9d4edd", "#f43f5e"],
                borderColor: "rgba(255,255,255,0.2)",
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: "#94a3b8" } } } }
    });

    // Monthly probability grid
    const grid = document.getElementById("monthlyProbGrid");
    grid.innerHTML = "";
    ms.forEach(m => {
        const div = document.createElement("div");
        div.className = "month-prob-card";
        // Color the circle border based on probability
        const hue = m.rain_percentage > 50 ? 210 : (m.rain_percentage > 25 ? 190 : 180);
        div.innerHTML = `
            <h4>${m.month_name}</h4>
            <div class="prob-circle" style="border-color: hsl(${hue}, 80%, 60%); color: hsl(${hue}, 80%, 60%);">
                ${m.rain_percentage}%
            </div>
            <div style="font-size: 11px; color: #64748b; margin-top: 4px;">
                ${m.rainy_days} rainy / ${m.total_days} total
            </div>
            <div style="font-size: 10px; color: #475569; margin-top: 2px;">
                ${m.prob_step}
            </div>`;
        grid.appendChild(div);
    });
}


// ─────────────────────────────────────────────────────────────
// NORMAL DISTRIBUTION TAB
// ─────────────────────────────────────────────────────────────
function renderNormalDist(d) {
    const n = d.normal_distribution;

    destroyChart("normalDist");
    charts.normalDist = new Chart(getCtx("normalDistChart"), {
        type: "line",
        data: {
            labels: n.pdf_curve.map(p => p.x),
            datasets: [{
                label: "Gaussian PDF f(x)",
                data:  n.pdf_curve.map(p => p.y),
                fill: true,
                backgroundColor: "rgba(157,78,221,0.15)",
                borderColor: "#9d4edd",
                borderWidth: 2.5,
                pointRadius: 0,
                tension: 0.4,
            }]
        },
        options: chartOpts("Probability Density")
    });

    setText("sigma1Text", `${n.sigma_1.low}°C to ${n.sigma_1.high}°C — ${n.sigma_1.count} days (${n.sigma_1.percentage}, expected ${n.sigma_1.expected})`);
    setText("sigma2Text", `${n.sigma_2.low}°C to ${n.sigma_2.high}°C — ${n.sigma_2.count} days (${n.sigma_2.percentage}, expected ${n.sigma_2.expected})`);
    setText("anomalyCount", `${n.anomaly_count} Days`);
}


// ─────────────────────────────────────────────────────────────
// TIME SERIES & TRENDS TAB
// ─────────────────────────────────────────────────────────────
function renderTimeSeries(d) {
    destroyChart("timeSeries");

    const step = 4;
    const dates = d.time_series.dates.filter((_,i) => i % step === 0);
    const temps = d.time_series.temps.filter((_,i) => i % step === 0);
    const ma7   = d.time_series.moving_avg_7.filter((_,i)  => i % step === 0);
    const ma30  = d.time_series.moving_avg_30.filter((_,i) => i % step === 0);
    const trend = d.time_series.trend_line.filter((_,i)    => i % step === 0);

    const reg = d.time_series.daily_regression;
    setText("regressionEquation", `${reg.equation}  (R² = ${reg.r_squared})`);

    // Show yearly regression step-by-step
    const regStep = document.getElementById("regressionStepBox");
    if (regStep) {
        const yr = d.time_series.yearly_regression;
        regStep.innerHTML = `
            <div class="calc-step-item"><strong>Yearly Regression:</strong> <span>${yr.equation}</span></div>
            <div class="calc-step-item" style="white-space:pre-wrap; font-size:12px; color:#94a3b8; margin-top:6px;">${yr.step}</div>`;
    }

    charts.timeSeries = new Chart(getCtx("timeSeriesChart"), {
        type: "line",
        data: {
            labels: dates,
            datasets: [
                { label: "Actual Temp (°C)",     data: temps, borderColor: "rgba(255,255,255,0.2)", borderWidth: 1,   pointRadius: 0 },
                { label: "7-Day Moving Avg",     data: ma7,   borderColor: "#4facfe",              borderWidth: 2,   pointRadius: 0 },
                { label: "30-Day Moving Avg",    data: ma30,  borderColor: "#00f2fe",              borderWidth: 2.5, pointRadius: 0 },
                { label: "Linear Trend (y=mx+c)",data: trend, borderColor: "#f43f5e",              borderWidth: 2.5, borderDash: [6,6], pointRadius: 0 },
            ]
        },
        options: chartOpts("Temperature Trend & Regression")
    });
}


// ─────────────────────────────────────────────────────────────
// FUTURE PREDICTION TAB
// ─────────────────────────────────────────────────────────────
function renderPrediction(d) {
    const tb = document.querySelector("#futurePredictionTable tbody");
    tb.innerHTML = "";
    d.future_predictions.forEach(p => {
        const tr = document.createElement("tr");
        const heatClass = p.heatwave_probability > 0.3 ? "rose" : "amber";
        tr.innerHTML = `
            <td><strong>${p.year}</strong></td>
            <td><strong>${p.predicted_avg_temp} °C</strong></td>
            <td>${p.predicted_precip} mm</td>
            <td>${p.predicted_rainy_days} Days</td>
            <td>${(p.rain_probability * 100).toFixed(1)}%</td>
            <td><span class="badge ${heatClass}">${(p.heatwave_probability * 100).toFixed(0)}%</span></td>`;
        tb.appendChild(tr);
    });
    updatePredictionCards(d.future_predictions[0].year);
}

function updatePredictionCards(year) {
    if (!currentAnalysisData) return;
    const pred = currentAnalysisData.future_predictions.find(p => p.year === year)
              || currentAnalysisData.future_predictions[0];
    const mean = currentAnalysisData.descriptive_stats.temperature.mean;
    const diff = (pred.predicted_avg_temp - mean).toFixed(1);

    setText("predTempDisplay",     `${pred.predicted_avg_temp} °C`);
    setText("predTempDiff",        `${diff >= 0 ? '+' + diff : diff}°C vs historical mean (${mean}°C)`);
    setText("predPrecipDisplay",   `${pred.predicted_precip} mm`);
    setText("predRainDaysDisplay", `${pred.predicted_rainy_days} Days`);
    setText("predRainProbDisplay", `${(pred.rain_probability * 100).toFixed(1)}% daily rain probability`);
    setText("predHeatwaveDisplay", `${(pred.heatwave_probability * 100).toFixed(0)}% Risk`);
}


// ─────────────────────────────────────────────────────────────
// VIVA & THEORY GUIDE TAB
// ─────────────────────────────────────────────────────────────
function loadVivaGuide() {
    fetch("/api/viva-guide")
        .then(r => r.json())
        .then(data => {
            if (data.status !== "success") return;
            const g = data.guide;

            const cards = document.getElementById("vivaCardsContainer");
            cards.innerHTML = "";
            g.concepts.forEach(c => {
                const div = document.createElement("div");
                div.className = "viva-card";
                div.innerHTML = `
                    <h3>${c.name}</h3>
                    <div class="stat-math-formula">$$${c.formula}$$</div>
                    <p style="font-size:13px; color:#94a3b8; margin-bottom:10px;">${c.description}</p>
                    <div class="viva-qbox">
                        <strong>Viva Q: ${c.viva_q}</strong>
                        <p style="margin-top:4px;"><strong>A:</strong> ${c.viva_a}</p>
                    </div>`;
                cards.appendChild(div);
            });

            const faq = document.getElementById("vivaFaqList");
            faq.innerHTML = "";
            g.viva_faq.forEach((f, i) => {
                const div = document.createElement("div");
                div.className = "viva-card";
                div.style.marginTop = "12px";
                div.innerHTML = `
                    <h4 style="color:#00f2fe; margin-bottom:6px;">Q${i + 1}: ${f.q}</h4>
                    <p style="font-size:14px; color:#e2e8f0;">${f.a}</p>`;
                faq.appendChild(div);
            });

            renderMath();
        });
}


// ─────────────────────────────────────────────────────────────
// RAW DATA TABLE & CSV EXPORT
// ─────────────────────────────────────────────────────────────
function renderRawData(d) {
    const tb = document.querySelector("#rawDataTable tbody");
    tb.innerHTML = "";

    // Show all records (paginated display — first 500 rows to avoid DOM overload)
    const records = d.raw_records.slice(0, 500);
    const totalLabel = document.getElementById("rawDataCountLabel");
    if (totalLabel) totalLabel.textContent = `Showing ${records.length} of ${d.raw_records.length} records`;

    records.forEach(r => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${r.date}</td>
            <td>${r.day_name}</td>
            <td><strong>${r.temp_mean} °C</strong></td>
            <td>${r.temp_max} °C</td>
            <td>${r.temp_min} °C</td>
            <td>${r.precipitation} mm</td>
            <td>${r.humidity}%</td>
            <td>${r.wind_speed} km/h</td>`;
        tb.appendChild(tr);
    });
}

function exportCSV() {
    if (!currentAnalysisData || !currentAnalysisData.raw_records) return;
    let csv = "Date,Day,Mean_Temp_C,Max_Temp_C,Min_Temp_C,Precipitation_mm,Humidity_pct,Wind_Speed_kmh\n";
    currentAnalysisData.raw_records.forEach(r => {
        csv += `${r.date},${r.day_name},${r.temp_mean},${r.temp_max},${r.temp_min},${r.precipitation},${r.humidity},${r.wind_speed}\n`;
    });
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${currentAnalysisData.metadata.city}_weather_${currentAnalysisData.metadata.start_year}_${currentAnalysisData.metadata.end_year}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}


// ─────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────
function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

function getCtx(id) {
    return document.getElementById(id).getContext("2d");
}

function destroyChart(key) {
    if (charts[key]) { charts[key].destroy(); charts[key] = null; }
}

function chartOpts(yTitle) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
            y: { title: { display: true, text: yTitle, color: "#94a3b8" }, ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
        },
        plugins: { legend: { labels: { color: "#94a3b8" } } }
    };
}
