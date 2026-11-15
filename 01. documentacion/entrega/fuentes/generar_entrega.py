"""Genera los PDF de entrega de AllpaShift (Summary, Project Details, AI and NASA Data, References).

Contenido en inglés (requisito de la NASA), basado en el proyecto real (repo, develop).
Uso:  python generar_entrega.py   → escribe los .html en fuentes/ y los .pdf en ../ con Chrome sin ventana.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI.parent
CHROME = next(p for p in [Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                          Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")] if p.exists())

ICONO = ('<svg viewBox="0 0 64 64" width="44" height="44"><rect width="64" height="64" rx="18" fill="#0f2a1f"/>'
         '<ellipse cx="32" cy="34" rx="25" ry="9" fill="none" stroke="#5b85f5" stroke-width="2" transform="rotate(-24 32 34)" opacity=".9"/>'
         '<path d="M32 50V30" stroke="#fff" stroke-width="4.5" stroke-linecap="round"/>'
         '<path d="M32 33c0-9 6-15 15-15 0 9-6 15-15 15z" fill="#c2ee5c"/>'
         '<path d="M32 39c0-7.5-5-12.5-13-12.5 0 8 5 13 13 12.5z" fill="#80cf9c"/><circle cx="52" cy="22" r="3.5" fill="#fff"/></svg>')

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@600;700;800&display=swap');
@page { size: A4; margin: 16mm 18mm 16mm 18mm; }
* { box-sizing: border-box; }
body { font-family: Inter, sans-serif; font-size: 10.2pt; line-height: 1.5; color: #1d2421; margin: 0; }
header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px solid #1d2421; padding-bottom: 12px; margin-bottom: 18px; }
.marca { display: flex; align-items: center; gap: 8px; font-family: Poppins; font-weight: 800; font-size: 21pt; color: #0f2a1f; }
.marca span { color: #2f9d27; }
.meta { text-align: right; font-size: 8.6pt; color: #4b5560; line-height: 1.55; }
.meta b { color: #1d2421; }
h1 { font-family: Poppins; font-weight: 800; font-size: 21pt; margin: 4px 0 2px; color: #1d2421; }
.sub { color: #5b6470; margin: 0 0 12px; }
h2 { font-family: Poppins; font-weight: 700; font-size: 13pt; margin: 16px 0 6px; }
h3 { font-family: Poppins; font-weight: 700; font-size: 11pt; margin: 12px 0 4px; }
p { margin: 4px 0 6px; }
.tag { font-family: Poppins; font-weight: 700; font-size: 12pt; color: #2f9d27; margin: 0 0 10px; }
.caja { border-left: 3px solid #2f9d27; background: #f3f6f2; padding: 7px 14px; margin: 6px 0 10px; }
ol, ul { margin: 4px 0 8px; padding-left: 22px; }
li { margin: 2px 0; }
li::marker { color: #2f9d27; font-weight: 600; }
.nuevo { display: inline-block; font-size: 7.4pt; font-weight: 600; color: #fff; background: #2f9d27; border-radius: 4px; padding: 0 5px; margin-left: 4px; vertical-align: 1px; }
table { width: 100%; border-collapse: collapse; margin: 6px 0 8px; font-size: 9pt; }
th { text-align: left; font-weight: 600; border-bottom: 1.5px solid #1d2421; padding: 5px 6px 5px 0; }
td { border-bottom: 1px solid #dde2dc; padding: 5px 6px 5px 0; vertical-align: top; }
td:first-child { font-weight: 600; width: 27%; }
.refs p { margin: 0 0 6px; font-size: 9pt; }
.lic td:first-child { width: 30%; } .lic td:nth-child(2) { width: 20%; font-weight: 400; }
.final { font-family: Poppins; font-weight: 700; color: #2f9d27; margin-top: 10px; }
.pie { margin-top: 14px; padding-top: 8px; border-top: 1px solid #dde2dc; font-size: 8pt; color: #6b7480; display: flex; justify-content: space-between; }
.salto { break-before: page; }
"""


def pagina(titulo: str, subtitulo: str, cuerpo: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>AllpaShift · {titulo}</title><style>{CSS}</style></head>
<body><header><div class="marca">{ICONO}<div>Allpa<span>Shift</span></div></div>
<div class="meta"><b>Team Halcón Dorado</b> · Piura, Peru<br>Challenge: Field Shift: Adapting Farms with NASA Data<br>NASA Space Apps Challenge 2026</div></header>
<h1>{titulo}</h1><p class="sub">{subtitulo}</p>{cuerpo}
<div class="pie"><span>AllpaShift · Team Halcón Dorado</span><span>NASA Space Apps Challenge 2026</span></div></body></html>"""


SUMMARY = pagina("High-Level Summary", "", """
<p class="tag">Plant for the climate that's coming, with NASA satellite data.</p>
<h2>What is the project?</h2>
<p>AllpaShift is a web and mobile app (Android and iOS) that turns NASA Earth observations into a simple decision for any farmer:
what to plant, when to plant it, and what to change when extreme weather is coming. The farmer picks a plot on a risk map, says
what matters most to them, and the app answers in plain language:</p>
<ul>
<li><b>What to do now.</b> One action for this fortnight (plant, wait, irrigate or protect), based on current field conditions.</li>
<li><b>Season risk.</b> Month-by-month risk from planting to harvest against drought, extreme rain, heat and El Niño.</li>
<li><b>What to change.</b> Crop rotations scored from 0 to 100 by climate risk <i>and</i> by their effect on soil health
(legumes, crop families, root depth, soil cover, no monoculture, salinity), using the soil type and salinity of the plot, and weighted by
the farmer's own priority: take less risk, save water or care for the soil. For permanent crops such as mango or lemon, it suggests actions for each growth stage.</li>
<li><b>Why.</b> Every result shows the NASA dataset behind it, and an AI assistant explains it in simple words without doing any of the calculations.</li>
</ul>
<p>It works at any coordinate on Earth. Piura, Peru, is our pilot.</p>
<h2>Why does it matter?</h2>
<p>Millions of small farmers still decide what to plant out of habit. When the climate changes, they lose more than a harvest: they lose a
whole year of investment and, with repeated monoculture, the health of their soil. In 2017 the coastal El Niño flooded the fields of Piura,
and farmers had no way to see it coming. The data needed to anticipate these events already exists and is free, but it does not reach the field.</p>
<h2>How does it address the challenge?</h2>
<p>Field Shift asks for a decision-support tool that combines NASA Earth observations with local soil information, crop characteristics
and farmer priorities to explore rotations that strengthen soil health. AllpaShift brings those four pieces together. Six NASA datasets drive it:
<b>NASA POWER</b> (temperature, rainfall, climatology), <b>GPM IMERG</b> (satellite rainfall, monthly and daily), <b>SMAP</b> (soil moisture),
<b>MODIS NDVI</b> (crop vigor) and <b>MUR SST</b> (sea temperature, the early El Niño signal). Applying today's rules to real 2017 data,
AllpaShift would have raised the El Niño alert weeks before the peak rains, and it shows the rain of every month, day by day, since 2001.</p>
<p class="final">We don't predict the weather. We prepare farmers, and their soil, for it.</p>
""")

DETAILS = pagina("Project Details", "How AllpaShift works, the tools we used and the goals behind it.", """
<h2>How does it work?</h2>
<div class="caja">The farmer picks a plot and sets priorities → the app (web, Android or iOS) calls the AllpaShift API → the API answers from
the database if the result is fresh, or asks the calculation service, which reads NASA data and applies fixed rules → the app shows what to do and why.</div>
<ol>
<li><b>Pick the plot.</b> The farmer taps a point on the map or uses the phone's GPS (native permission on Android and iOS). It works at any coordinate on Earth.</li>
<li><b>Set the priority.</b><span class="nuevo">NEW</span> The farmer chooses what matters most: take less risk, save water or care for the soil. This changes the weights of the final score and the recommended rotation, and the app says why.</li>
<li><b>Get the data.</b> Rainfall, temperature and climatology from NASA POWER for any point. In the Piura pilot area it adds GPM IMERG
satellite rainfall, SMAP soil moisture and MODIS NDVI vegetation; on the northern coast, MUR SST sea temperature.</li>
<li><b>Know the local soil.</b><span class="nuevo">NEW</span> The farmer marks the soil type (sandy, loam, clay) and salinity of the plot. The app suggests the soil type
from SoilGrids (ISRIC, sand/silt/clay at 0–30 cm) and labels it as such, never as NASA data. SMAP adds the current soil moisture.</li>
<li><b>Compute the indicators.</b> Rainfall, soil moisture, heat, El Niño and vegetation compare the current value with the normal for that month and get a level: low, medium or high.</li>
<li><b>Estimate season risk.</b> For each crop, from planting to harvest, the climate of each month is compared with what the crop tolerates. If sea temperature signals El Niño, rain risk from January to April goes up.</li>
<li><b>Score the rotations: climate, soil health and water.</b><span class="nuevo">NEW</span> The climate score starts at 100 and loses points for water needs versus deficit,
months outside the temperature range, high-risk months and planting out of season. The soil-health score rewards nitrogen-fixing legumes (e.g. cowpea, lablab),
alternating root depths and soil cover, and penalizes monoculture, two crops of the same family, two water-hungry crops in a row, and salt-sensitive crops on
saline or sandy soil (crop traits from FAO-56 and FAO Irrigation and Drainage Paper 29). The final score weights climate, soil and water by the farmer's priority.
For each rotation the app lists benefits, risks and trade-offs, what we don't know, and what to check with a local expert.</li>
<li><b>Decide and explain.</b> Priority rules choose the action for this fortnight. The app shows the result with its NASA dataset, and an AI assistant explains it in plain words. The AI does no calculations.</li>
</ol>
<h3>Validation with the 2017 El Niño</h3>
<p>We applied the same rules to real data from 2001 to 2026. Rainfall comes from GPM IMERG and the alert from the MUR SST series. Tapping any
month shows its rain day by day and week by week (IMERG daily), so the farmer can see exactly when the heaviest rains fell.</p>
<h3>What the system does not do</h3>
<p>AllpaShift does not forecast exact weather months ahead: it estimates risk from NASA climate history and the early El Niño signal.
It does not replace a soil laboratory test. Thresholds and soil-health weights are team assumptions, documented in the code so they can be adjusted.</p>
<h2 class="salto">What tools did we use?</h2>
<table><tr><th>Component</th><th>Tools</th></tr>
<tr><td>App (web, Android, iOS)</td><td>Vue 3, Vite, TypeScript, Tailwind CSS, Pinia, vue-i18n (Spanish and English), Leaflet for the map, Chart.js for charts and Capacitor for Android and iOS.</td></tr>
<tr><td>AllpaShift API</td><td>Java 17 with Spring Boot and Spring Cloud Gateway. It is the only component that reads and writes the database, and answers from it when data is fresh.</td></tr>
<tr><td>Database</td><td>PostgreSQL: crop catalog, zones, rotations, saved results and every NASA value used.</td></tr>
<tr><td>Calculation service</td><td>Python with FastAPI, Pydantic, httpx, pandas and NumPy. Rules and thresholds in configuration files, with automated tests (pytest). It only reads NASA data and calculates.</td></tr>
<tr><td>NASA data access</td><td>NASA POWER API; NASA Earthdata (CMR and OPeNDAP) for GPM IMERG and SMAP; ORNL DAAC MODIS web service for NDVI; MUR SST v4.1 (NASA JPL, PO.DAAC) through NOAA CoastWatch ERDDAP.</td></tr>
<tr><td>AI assistant</td><td>Groq as the platform, with the open model gpt-oss-20b (Apache 2.0). It only writes explanations from results that are already calculated.</td></tr>
<tr><td>Deployment</td><td>Docker and Nginx on a cloud server.</td></tr>
<tr><td>Soil data</td><td>SoilGrids 2.0 REST API (ISRIC, CC-BY 4.0) to suggest the soil type; the farmer can change it.</td></tr>
<tr><td>Maps and collaboration</td><td>OpenStreetMap data and place search (ODbL, with attribution). GitHub for code and version control.</td></tr></table>
<p>All project code is released under the Apache 2.0 license.</p>
<h2>Goals</h2>
<ul>
<li>Help farmers decide what to plant based on data, not just habit.</li>
<li>Choose rotations that protect and rebuild the soil, not only the next harvest.</li>
<li>Respect what each farmer values most: lower risk, saving water or caring for the soil.</li>
<li>Reduce harvest losses from drought, extreme rain, heat and El Niño, and warn early using sea temperature.</li>
<li>Make NASA data easy to understand for people without technical training, in any farming region of the world.</li>
</ul>
""")

AI_NASA = pagina("Use of AI and NASA Data", "Which NASA data we use, how we use it, and how we use artificial intelligence.", """
<h2>NASA data</h2>
<p>AllpaShift uses six open NASA datasets. Every calculation (indicators, season risk, rotation scores and alerts) comes from these data and
the crop and soil catalog through fixed rules, with no AI.</p>
<table><tr><th>Dataset</th><th>Variables</th><th>How it contributes</th></tr>
<tr><td>NASA POWER (API, Agroclimatology)</td><td>PRECTOTCORR, GWETTOP, T2M_MAX, T2M_MIN; daily data and climatology</td><td>Heat indicator and rainfall/soil moisture at any coordinate. Its climatology defines "normal" and the risk of each month of the season.</td></tr>
<tr><td>GPM IMERG V07: Final monthly (GPM_3IMERGM), Final daily (GPM_3IMERGDF), Late daily (GPM_3IMERGDL)</td><td>precipitation</td><td>Current satellite rainfall in the Piura pilot, monthly series 2001–2026 for validation, and day-by-day rain of any month.</td></tr>
<tr><td>SMAP L3 Enhanced (SPL3SMP_E V006, 9 km)</td><td>soil_moisture (AM and PM passes)</td><td>Current soil moisture versus its 2016–2025 normal. Drives the "wait / irrigate" action, water penalties and the local soil picture.</td></tr>
<tr><td>MODIS Terra NDVI (MOD13Q1 V061, 250 m)</td><td>250m_16_days_NDVI</td><td>Vegetation indicator: crop vigor versus the normal for the same 16-day period; low vigor or bare soil signals stress and soil-cover needs.</td></tr>
<tr><td>MUR SST v4.1 (NASA JPL, PO.DAAC, via NOAA ERDDAP)</td><td>analysed_sst, sstAnom over Niño 1+2</td><td>El Niño indicator: raises rain risk from January to April, triggers "prepare drainage" and dates the 2017 alert.</td></tr></table>
<p>Partner space agencies: we do not use partner agency data. NOAA ERDDAP is only the access channel for MUR SST, a NASA JPL product.
Local soil information comes from the farmer (soil type and salinity), with a soil type suggested by SoilGrids 2.0 (ISRIC, CC-BY 4.0), always labelled as
not NASA data. Crop traits (water use, temperature range, family, root depth, salt tolerance) come from the team's catalog, built from FAO-56, FAO Irrigation and
Drainage Paper 29 and Peruvian agricultural sources listed in References.</p>
<h2>How we use the data, step by step</h2>
<ol>
<li>The farmer picks a plot and priorities; the app sends them to the AllpaShift API.</li>
<li>If a fresh result is stored, the API answers from the database (the demo does not depend on NASA servers being up).</li>
<li>Otherwise the calculation service reads the NASA datasets for that point and compares each value with its normal: low, medium or high.</li>
<li>The climatology, local soil and crop traits are used to estimate season risk and to score rotations for climate and soil health, ranked by the farmer's priorities.</li>
<li>The API stores the result and every NASA value used; the app shows each result with the dataset it comes from.</li>
</ol>
<p>If a value is not available for a place or date, the app shows "no data" and never replaces it with invented values.</p>
<h2 class="salto">Use of artificial intelligence</h2>
<p>We use AI at two points: inside the app, to explain recommendations, and during development, to support the team. AI never calculates the indicators, scores or alerts.</p>
<table><tr><th>Tool</th><th>Purpose</th><th>How we applied it</th></tr>
<tr><td>Groq with gpt-oss-20b (Apache 2.0)</td><td>In-app assistant that explains the recommendation in plain words.</td><td>It receives the already-calculated recommendation as JSON plus the farmer's question. It is told not to calculate, not to invent numbers and to cite only the sources in the JSON; numbers in the answer are checked. If it fails, the app shows the calculated reason. The API key stays on the server.</td></tr>
<tr><td>Claude (Anthropic)</td><td>Writing part of the code (frontend, API, calculation service, mobile) and documentation drafts.</td><td>The team defined the architecture, rules and data. It reviewed, tested and fixed the generated code, and verified it with automated tests.</td></tr>
<tr><td>ChatGPT (OpenAI)</td><td>Visual support: cover image and AllpaShift icon.</td><td>Visual illustration only; it does not represent real data.</td></tr></table>
<p>All AI-generated content was reviewed by the team. The ideas, decisions and data in this project belong to Team Halcón Dorado.</p>
<h2>Links</h2>
<table class="lic"><tr><td>NASA POWER</td><td colspan="2">https://power.larc.nasa.gov/</td></tr>
<tr><td>GPM IMERG</td><td colspan="2">https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary · GPM_3IMERGDF_07 · GPM_3IMERGDL_07</td></tr>
<tr><td>SMAP SPL3SMP_E</td><td colspan="2">https://nsidc.org/data/spl3smp_e/versions/6</td></tr>
<tr><td>MODIS MOD13Q1</td><td colspan="2">https://lpdaac.usgs.gov/products/mod13q1v061/</td></tr>
<tr><td>MUR SST v4.1</td><td colspan="2">https://podaac.jpl.nasa.gov/dataset/MUR-JPL-L4-GLOB-v4.1</td></tr></table>
""")

REFERENCES = pagina("References", "All data, resources and external tools used in AllpaShift, with their licenses.", """
<div class="refs">
<h2>NASA data</h2>
<p>NASA Langley Research Center. POWER Project (Prediction Of Worldwide Energy Resources), Agroclimatology community, API v2. Open data. https://power.larc.nasa.gov/</p>
<p>Huffman, G. J., et al. GPM IMERG Final Precipitation L3 1 month 0.1° x 0.1° V07 (GPM_3IMERGM). NASA GES DISC. https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07</p>
<p>Huffman, G. J., et al. GPM IMERG Final Precipitation L3 1 day 0.1° x 0.1° V07 (GPM_3IMERGDF). NASA GES DISC. https://doi.org/10.5067/GPM/IMERGDF/DAY/07</p>
<p>Huffman, G. J., et al. GPM IMERG Late Precipitation L3 1 day 0.1° x 0.1° V07 (GPM_3IMERGDL). NASA GES DISC. https://doi.org/10.5067/GPM/IMERGDL/DAY/07</p>
<p>O'Neill, P. E., et al. SMAP Enhanced L3 Radiometer Global Daily 9 km EASE-Grid Soil Moisture, Version 6 (SPL3SMP_E). NASA NSIDC DAAC. https://doi.org/10.5067/M20OXIZHY3RJ</p>
<p>Didan, K. MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061 (MOD13Q1). NASA LP DAAC. https://doi.org/10.5067/MODIS/MOD13Q1.061 — accessed through the ORNL DAAC MODIS Web Service, https://modis.ornl.gov/</p>
<p>JPL MUR MEaSUREs Project. GHRSST Level 4 MUR Global Foundation Sea Surface Temperature Analysis (v4.1). NASA PO.DAAC. https://doi.org/10.5067/GHGMR-4FJ04</p>
<p>NOAA CoastWatch. ERDDAP, used to access the MUR SST subset (jplMURSST41, jplMURSST41anom1day). U.S. Government public domain. https://coastwatch.pfeg.noaa.gov/erddap/</p>
<h2>Other sources</h2>
<p>INDECI, National Civil Defense Institute of Peru. Reports on the damage of the 2017 coastal El Niño in Piura. https://www.gob.pe/indeci</p>
<p>FAO. ECOCROP, crop temperature and water requirements, and Global Agro-Ecological Zones (GAEZ v4), used as reference for the crop catalog. https://gaez.fao.org/</p>
<p>DRAP Piura / MIDAGRI, Peru. Regional agricultural statistics: sown area by crop and valley, used for the catalog of zones, crops and common rotations. https://www.gob.pe/midagri</p>
<p>Poggio, L., et al. (2021). SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. SOIL 7, 217–240. https://doi.org/10.5194/soil-7-217-2021 — ISRIC REST API, CC-BY 4.0, https://rest.isric.org</p>
<p>Allen, R. G., Pereira, L. S., Raes, D., Smith, M. (1998). Crop evapotranspiration (FAO Irrigation and Drainage Paper 56): root depth and crop coefficients. https://www.fao.org/4/x0490e/x0490e00.htm</p>
<p>Ayers, R. S., Westcot, D. W. (1985). Water quality for agriculture (FAO Irrigation and Drainage Paper 29): crop salt tolerance. https://www.fao.org/4/t0234e/t0234e00.htm</p>
<p>NOAA Climate Prediction Center. Weekly Niño indices, used to cross-check MUR SST. https://www.cpc.ncep.noaa.gov/data/indices/</p>
<p>OpenStreetMap contributors. Map data and place search (Nominatim). ODbL license, with attribution on the map. https://www.openstreetmap.org/copyright</p>
</div>
<h2>App software (web and mobile)</h2>
<table class="lic"><tr><th>Tool</th><th>License</th><th>Link</th></tr>
<tr><td>Vue 3 · Vue Router · Pinia</td><td>MIT</td><td>https://github.com/vuejs</td></tr>
<tr><td>Vite</td><td>MIT</td><td>https://github.com/vitejs/vite</td></tr>
<tr><td>TypeScript</td><td>Apache-2.0</td><td>https://github.com/microsoft/TypeScript</td></tr>
<tr><td>Tailwind CSS</td><td>MIT</td><td>https://github.com/tailwindlabs/tailwindcss</td></tr>
<tr><td>vue-i18n · Axios</td><td>MIT</td><td>https://github.com/intlify/vue-i18n · https://github.com/axios/axios</td></tr>
<tr><td>Chart.js · vue-chartjs</td><td>MIT</td><td>https://github.com/chartjs/Chart.js</td></tr>
<tr><td>Leaflet</td><td>BSD-2-Clause</td><td>https://github.com/Leaflet/Leaflet</td></tr>
<tr><td>Lucide (icons)</td><td>ISC</td><td>https://github.com/lucide-icons/lucide</td></tr>
<tr><td>Capacitor (Android and iOS)</td><td>MIT</td><td>https://github.com/ionic-team/capacitor</td></tr>
<tr><td>Fonts Inter and Bricolage Grotesque</td><td>OFL-1.1</td><td>https://fonts.google.com/</td></tr></table>
<h2>API, database and deployment</h2>
<table class="lic"><tr><th>Tool</th><th>License</th><th>Link</th></tr>
<tr><td>Spring Boot · Spring Cloud Gateway</td><td>Apache-2.0</td><td>https://github.com/spring-projects</td></tr>
<tr><td>Jackson</td><td>Apache-2.0</td><td>https://github.com/FasterXML/jackson</td></tr>
<tr><td>PostgreSQL</td><td>PostgreSQL License</td><td>https://www.postgresql.org/about/licence/</td></tr>
<tr><td>Docker Engine</td><td>Apache-2.0</td><td>https://github.com/moby/moby</td></tr>
<tr><td>Nginx</td><td>BSD-2-Clause</td><td>https://nginx.org/LICENSE</td></tr></table>
<h2>Calculation service (Python)</h2>
<table class="lic"><tr><th>Tool</th><th>License</th><th>Link</th></tr>
<tr><td>FastAPI · Pydantic</td><td>MIT</td><td>https://github.com/fastapi/fastapi</td></tr>
<tr><td>Uvicorn · httpx</td><td>BSD-3-Clause</td><td>https://github.com/encode</td></tr>
<tr><td>pandas · NumPy</td><td>BSD-3-Clause</td><td>https://github.com/pandas-dev/pandas</td></tr>
<tr><td>xarray</td><td>Apache-2.0</td><td>https://github.com/pydata/xarray</td></tr>
<tr><td>netCDF4 · earthaccess · PyYAML · pytest</td><td>MIT</td><td>https://github.com/nsidc/earthaccess</td></tr>
<tr><td>h5netcdf</td><td>BSD-3-Clause</td><td>https://github.com/h5netcdf/h5netcdf</td></tr></table>
<h2>Artificial intelligence</h2>
<table class="lic"><tr><th>Tool</th><th>License or terms</th><th>Link</th></tr>
<tr><td>gpt-oss-20b (OpenAI), in-app assistant model</td><td>Apache-2.0</td><td>https://huggingface.co/openai/gpt-oss-20b</td></tr>
<tr><td>Groq, platform that runs the model</td><td>Groq terms of service</td><td>https://groq.com/</td></tr>
<tr><td>Claude (Anthropic), help writing code and documents</td><td>Service</td><td>https://claude.ai/</td></tr>
<tr><td>ChatGPT (OpenAI), cover and icon</td><td>Service</td><td>https://chatgpt.com/</td></tr></table>
<h2>Project license</h2>
<p>AllpaShift original code is released under the Apache 2.0 license and managed on GitHub: https://github.com/jramirezch1978/allpashift</p>
""")

DOCS = {
    "AllpaShift_Summary": SUMMARY,
    "AllpaShift_Project_Details_EN": DETAILS,
    "AllpaShift_AI_and_NASA_Data_EN": AI_NASA,
    "AllpaShift_References_EN": REFERENCES,
}

if __name__ == "__main__":
    for nombre, html in DOCS.items():
        h = AQUI / f"{nombre}.html"
        h.write_text(html, encoding="utf-8")
        pdf = SALIDA / f"{nombre}.pdf"
        subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--virtual-time-budget=8000", f"--print-to-pdf={pdf}", h.as_uri()],
                       check=True, capture_output=True, timeout=120)
        print("OK", pdf.name)
