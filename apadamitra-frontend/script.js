 /* ═══════════════════════════════════════════════════════════════
   APADAMITRA — script.js
   AI Disaster Prediction & Mitigation System
   Compatible with index.html + style.css
   Backend: http://127.0.0.1:8000
   ═══════════════════════════════════════════════════════════════ */

// ─── CONFIG ──────────────────────────────────────────────────────
const BASE_URL = 'http://127.0.0.1:8000';
const WEATHER_API_KEY = 'd57d87b657720d7164187465070f0b7d'; // Replace with your key
const WEATHER_API = 'https://api.openweathermap.org/data/2.5/weather';

// ─── STATE ───────────────────────────────────────────────────────
let currentLang = 'en';
const langMap = {
  en: "en",
  hi: "hi",
  bn: "bn"
};
let currentUserType = 'farmer';
let currentLat = null;
let currentLon = null;
let currentDisaster = null;   // null = clear | 'flood' | 'cyclone' | 'heatwave'
let isSimulating = false;
let map = null;
let mapLayers = { safe: [], warn: [], danger: [] };
let userMarker = null;
let recognition = null;
let isListening = false;
let speechSynth = window.speechSynthesis;

// ─── I18N STRINGS ────────────────────────────────────────────────
const i18n = {
  en: {
    nav_weather: 'Weather', nav_mitigation: 'Mitigation',
    nav_voice: 'AI Assistant', nav_map: 'Safety Map',
    hero_badge: '⚡ AI-Powered Emergency Intelligence',
    hl1: 'Predict.', hl2: 'Protect.', hl3: 'Survive.',
    hero_body: 'APADAMITRA harnesses advanced AI to detect floods, cyclones, and heatwaves before they strike — delivering personalized guidance in your language, exactly when it matters most.',
    cta_live: 'Check Live Safety', cta_ai: 'Talk to AI Assistant',
    stat_disasters: 'Disaster Types', stat_monitor: 'AI Monitoring', stat_langs: 'Languages',
    sec_tag_live: 'Live Intelligence', weather_title: 'Weather Monitoring',
    weather_desc: 'Real-time atmospheric intelligence for your region',
    detecting_loc: 'Detecting location...',
    w_temp: 'Temperature', w_humidity: 'Humidity', w_wind: 'Wind Speed',
    w_pressure: 'Air Pressure', w_visibility: 'Visibility',
    w_condition: 'Condition', w_rain: 'Rain Probability', w_uv: 'UV Index',
    sec_tag_ai: 'AI Analysis', pred_title: 'Disaster Intelligence Hub',
    pred_desc: 'Advanced AI threat assessment for your location',
    prob_flood: 'Flood Probability', prob_cyclone: 'Cyclone Probability', prob_heat: 'Heatwave Probability',
    badge_clear: 'ALL CLEAR', status_safe_title: 'No Immediate Threat Detected',
    status_safe_desc: 'Your area is currently safe. APADAMITRA AI is actively monitoring atmospheric conditions around the clock.',
    refresh_analysis: 'Refresh Analysis', live_monitoring: 'Live Monitoring',
    demo_mode: 'DEMO SIMULATION MODE',
    demo_sub: 'Showcase disaster scenarios for live demonstrations',
    sim_flood: 'Simulate Flood', sim_cyclone: 'Simulate Cyclone',
    sim_heat: 'Simulate Heatwave', sim_reset: 'Reset / All Clear',
    sec_tag_guidance: 'AI Guidance', mit_title: 'Mitigation Strategies',
    mit_desc: 'Personalized emergency guidance tailored to your profile',
    mit_ph_title: 'Awaiting Threat Assessment',
    mit_ph_desc: 'Run a prediction or simulate a disaster scenario to receive personalized mitigation strategies in your language.',
    run_now: 'Run Analysis Now',
    sev_label: 'Severity Level:',
    mit_do: 'What To Do', mit_dont: 'What NOT To Do', mit_kit: 'Emergency Kit',
    listen_btn: 'Listen',
    sec_tag_geo: 'Geospatial Intelligence', map_title: 'Safety Intelligence Map',
    map_safe: '✅ You are currently in a safe zone.',
    map_danger: '🚨 Danger zones detected in your region.',
    safe_zone: 'Safe Zone', warn_zone: 'Warning Zone', danger_zone: 'Danger Zone',
    modal_title: 'APADAMITRA AI', modal_sub: 'Emergency Intelligence Assistant',
    ai_greeting: "Namaste! I'm APADAMITRA AI. Ask me about disaster preparedness, safety tips, or real-time weather conditions in your area.",
    listening: 'Listening...',
    flood_alert: 'Flood Warning Detected',
    cyclone_alert: 'Cyclone Risk High',
    heat_alert: 'Extreme Heatwave Alert',
    flood_desc: 'Severe flooding conditions predicted. Immediate action required. Move to higher ground and follow emergency protocols.',
    cyclone_desc: 'Cyclonic storm approaching. Dangerous wind speeds and heavy rain expected. Seek shelter immediately.',
    heat_desc: 'Extreme heat conditions detected. Heat index dangerously high. Stay indoors and hydrate frequently.',
  },
  hi: {
    nav_weather: 'मौसम', nav_mitigation: 'शमन', nav_voice: 'AI सहायक', nav_map: 'सुरक्षा मानचित्र',
    hero_badge: '⚡ AI-संचालित आपातकालीन सूचना',
    hl1: 'पूर्वानुमान।', hl2: 'सुरक्षा।', hl3: 'जीवन।',
    hero_body: 'APADAMITRA उन्नत AI का उपयोग करके बाढ़, चक्रवात और लू का पता लगाता है — आपकी भाषा में व्यक्तिगत मार्गदर्शन प्रदान करता है।',
    cta_live: 'लाइव सुरक्षा जाँचें', cta_ai: 'AI सहायक से बात करें',
    stat_disasters: 'आपदा प्रकार', stat_monitor: 'AI निगरानी', stat_langs: 'भाषाएँ',
    sec_tag_live: 'लाइव इंटेलिजेंस', weather_title: 'मौसम निगरानी',
    weather_desc: 'आपके क्षेत्र के लिए वास्तविक समय वायुमंडलीय जानकारी',
    detecting_loc: 'स्थान पहचाना जा रहा है...',
    w_temp: 'तापमान', w_humidity: 'आर्द्रता', w_wind: 'हवा की गति',
    w_pressure: 'वायु दाब', w_visibility: 'दृश्यता',
    w_condition: 'स्थिति', w_rain: 'वर्षा संभावना', w_uv: 'UV सूचकांक',
    sec_tag_ai: 'AI विश्लेषण', pred_title: 'आपदा सूचना केंद्र',
    pred_desc: 'आपके स्थान के लिए उन्नत AI खतरा मूल्यांकन',
    prob_flood: 'बाढ़ संभावना', prob_cyclone: 'चक्रवात संभावना', prob_heat: 'लू संभावना',
    badge_clear: 'सब सुरक्षित', status_safe_title: 'कोई तत्काल खतरा नहीं',
    status_safe_desc: 'आपका क्षेत्र वर्तमान में सुरक्षित है। APADAMITRA AI चौबीसों घंटे निगरानी कर रहा है।',
    refresh_analysis: 'विश्लेषण रीफ्रेश करें', live_monitoring: 'लाइव निगरानी',
    demo_mode: 'डेमो सिमुलेशन मोड',
    demo_sub: 'लाइव प्रदर्शन के लिए आपदा परिदृश्य दिखाएं',
    sim_flood: 'बाढ़ सिमुलेट करें', sim_cyclone: 'चक्रवात सिमुलेट करें',
    sim_heat: 'लू सिमुलेट करें', sim_reset: 'रीसेट / सब सुरक्षित',
    sec_tag_guidance: 'AI मार्गदर्शन', mit_title: 'शमन रणनीतियाँ',
    mit_desc: 'आपकी प्रोफ़ाइल के अनुसार व्यक्तिगत आपातकालीन मार्गदर्शन',
    mit_ph_title: 'खतरा मूल्यांकन की प्रतीक्षा',
    mit_ph_desc: 'अपनी भाषा में व्यक्तिगत शमन रणनीतियाँ पाने के लिए पूर्वानुमान चलाएं।',
    run_now: 'अभी विश्लेषण करें',
    sev_label: 'गंभीरता स्तर:',
    mit_do: 'क्या करें', mit_dont: 'क्या न करें', mit_kit: 'आपातकालीन किट',
    listen_btn: 'सुनें',
    sec_tag_geo: 'भू-स्थानिक बुद्धिमत्ता', map_title: 'सुरक्षा मानचित्र',
    map_safe: '✅ आप वर्तमान में एक सुरक्षित क्षेत्र में हैं।',
    map_danger: '🚨 आपके क्षेत्र में खतरनाक क्षेत्र पाए गए।',
    safe_zone: 'सुरक्षित क्षेत्र', warn_zone: 'चेतावनी क्षेत्र', danger_zone: 'खतरनाक क्षेत्र',
    modal_title: 'APADAMITRA AI', modal_sub: 'आपातकालीन सूचना सहायक',
    ai_greeting: 'नमस्ते! मैं APADAMITRA AI हूँ। आपदा तैयारी, सुरक्षा युक्तियाँ, या मौसम के बारे में पूछें।',
    listening: 'सुन रहा हूँ...',
    flood_alert: 'बाढ़ की चेतावनी जारी', cyclone_alert: 'चक्रवात का खतरा अधिक', heat_alert: 'अत्यधिक लू की चेतावनी',
    flood_desc: 'गंभीर बाढ़ की स्थिति। तुरंत ऊँचे स्थान पर जाएं।', cyclone_desc: 'चक्रवाती तूफान आ रहा है। तुरंत आश्रय लें।', heat_desc: 'अत्यधिक गर्मी की स्थिति। घर के अंदर रहें और पानी पियें।',
  },
  bn: {
    nav_weather: 'আবহাওয়া', nav_mitigation: 'প্রশমন', nav_voice: 'AI সহকারী', nav_map: 'নিরাপত্তা মানচিত্র',
    hero_badge: '⚡ AI-চালিত জরুরি বুদ্ধিমত্তা',
    hl1: 'পূর্বাভাস।', hl2: 'সুরক্ষা।', hl3: 'বেঁচে থাকো।',
    hero_body: 'APADAMITRA উন্নত AI ব্যবহার করে বন্যা, ঘূর্ণিঝড় এবং তাপপ্রবাহ শনাক্ত করে — আপনার ভাষায় ব্যক্তিগতকৃত নির্দেশনা প্রদান করে।',
    cta_live: 'লাইভ নিরাপত্তা পরীক্ষা করুন', cta_ai: 'AI সহকারীর সাথে কথা বলুন',
    stat_disasters: 'দুর্যোগের ধরন', stat_monitor: 'AI পর্যবেক্ষণ', stat_langs: 'ভাষা',
    sec_tag_live: 'লাইভ ইন্টেলিজেন্স', weather_title: 'আবহাওয়া পর্যবেক্ষণ',
    weather_desc: 'আপনার অঞ্চলের জন্য রিয়েল-টাইম বায়ুমণ্ডলীয় তথ্য',
    detecting_loc: 'অবস্থান শনাক্ত হচ্ছে...',
    w_temp: 'তাপমাত্রা', w_humidity: 'আর্দ্রতা', w_wind: 'বায়ু গতি',
    w_pressure: 'বায়ু চাপ', w_visibility: 'দৃশ্যমানতা',
    w_condition: 'অবস্থা', w_rain: 'বৃষ্টির সম্ভাবনা', w_uv: 'UV সূচক',
    sec_tag_ai: 'AI বিশ্লেষণ', pred_title: 'দুর্যোগ বুদ্ধিমত্তা কেন্দ্র',
    pred_desc: 'আপনার অবস্থানের জন্য উন্নত AI হুমকি মূল্যায়ন',
    prob_flood: 'বন্যার সম্ভাবনা', prob_cyclone: 'ঘূর্ণিঝড়ের সম্ভাবনা', prob_heat: 'তাপপ্রবাহের সম্ভাবনা',
    badge_clear: 'সব নিরাপদ', status_safe_title: 'কোনো তাৎক্ষণিক হুমকি নেই',
    status_safe_desc: 'আপনার এলাকা বর্তমানে নিরাপদ। APADAMITRA AI চব্বিশ ঘণ্টা পর্যবেক্ষণ করছে।',
    refresh_analysis: 'বিশ্লেষণ রিফ্রেশ করুন', live_monitoring: 'লাইভ পর্যবেক্ষণ',
    demo_mode: 'ডেমো সিমুলেশন মোড',
    demo_sub: 'লাইভ প্রদর্শনের জন্য দুর্যোগের পরিস্থিতি দেখান',
    sim_flood: 'বন্যা সিমুলেট করুন', sim_cyclone: 'ঘূর্ণিঝড় সিমুলেট করুন',
    sim_heat: 'তাপপ্রবাহ সিমুলেট করুন', sim_reset: 'রিসেট / সব নিরাপদ',
    sec_tag_guidance: 'AI নির্দেশনা', mit_title: 'প্রশমন কৌশল',
    mit_desc: 'আপনার প্রোফাইল অনুযায়ী ব্যক্তিগতকৃত জরুরি নির্দেশনা',
    mit_ph_title: 'হুমকি মূল্যায়নের অপেক্ষা',
    mit_ph_desc: 'আপনার ভাষায় ব্যক্তিগতকৃত প্রশমন কৌশল পেতে পূর্বাভাস চালান।',
    run_now: 'এখনই বিশ্লেষণ করুন',
    sev_label: 'তীব্রতার স্তর:',
    mit_do: 'কী করবেন', mit_dont: 'কী করবেন না', mit_kit: 'জরুরি কিট',
    listen_btn: 'শুনুন',
    sec_tag_geo: 'ভূ-স্থানিক বুদ্ধিমত্তা', map_title: 'নিরাপত্তা মানচিত্র',
    map_safe: '✅ আপনি বর্তমানে একটি নিরাপদ এলাকায় আছেন।',
    map_danger: '🚨 আপনার অঞ্চলে বিপদ এলাকা শনাক্ত হয়েছে।',
    safe_zone: 'নিরাপদ এলাকা', warn_zone: 'সতর্কতা এলাকা', danger_zone: 'বিপদ এলাকা',
    modal_title: 'APADAMITRA AI', modal_sub: 'জরুরি বুদ্ধিমত্তা সহকারী',
    ai_greeting: 'নমস্কার! আমি APADAMITRA AI। দুর্যোগ প্রস্তুতি, নিরাপত্তা টিপস, বা আবহাওয়া সম্পর্কে জিজ্ঞেস করুন।',
    listening: 'শুনছি...',
    flood_alert: 'বন্যার সতর্কতা জারি হয়েছে', cyclone_alert: 'ঘূর্ণিঝড়ের ঝুঁকি বেশি', heat_alert: 'অতিরিক্ত তাপপ্রবাহ সতর্কতা',
    flood_desc: 'গুরুতর বন্যার পরিস্থিতি। অবিলম্বে উঁচু স্থানে যান।', cyclone_desc: 'ঘূর্ণিঝড় এগিয়ে আসছে। তাৎক্ষণিক আশ্রয় নিন।', heat_desc: 'অতিরিক্ত গরম পরিস্থিতি। ঘরে থাকুন এবং বারবার পানি পান করুন।',
  }
};

// ─── SPEECH LANG CODES ───────────────────────────────────────────
const speechLangCodes = { en: 'en-IN', hi: 'hi-IN', bn: 'bn-IN' };

// ─── HELPERS ─────────────────────────────────────────────────────
function t(key) {
  return (i18n[currentLang] && i18n[currentLang][key]) || (i18n.en[key]) || key;
}

function applyI18n() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const val = t(key);
    if (val) el.textContent = val;
  });
  // Placeholder for chat input
  const ci = document.getElementById('chatInput');
  if (ci) ci.placeholder = currentLang === 'hi' ? 'अपना प्रश्न टाइप या बोलें...' : currentLang === 'bn' ? 'প্রশ্ন টাইপ বা বলুন...' : 'Type or speak your question...';
}

function showToast(msg, type = 'info') {
  const wrap = document.getElementById('toastWrap');
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  wrap.appendChild(t);
  setTimeout(() => t.classList.add('show'), 50);
  setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 400); }, 3500);
}

function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ─── LANGUAGE & USER TYPE ────────────────────────────────────────
function setLanguage(lang) {
  currentLang = lang;
  document.documentElement.lang = lang;
  applyI18n();
  // If mitigation is visible, re-speak greeting update
  const greet = document.getElementById('greetingText');
  if (greet) greet.textContent = t('ai_greeting');
  // Reapply map status
  const mapMsg = document.getElementById('mapStatusMsg');
  if (mapMsg) mapMsg.textContent = (currentDisaster && isSimulating) ? t('map_danger') : t('map_safe');
  showToast(lang === 'hi' ? 'भाषा बदली गई' : lang === 'bn' ? 'ভাষা পরিবর্তিত হয়েছে' : 'Language updated', 'info');
}

function setUserType(type) {
  currentUserType = type;
  // If there's an active disaster, refresh mitigation
  if (currentDisaster) {
    fetchMitigation(currentDisaster, 75);
  }
}

// ─── LOADING SCREEN ──────────────────────────────────────────────
function hideLoadingScreen() {
  const ls = document.getElementById('loadingScreen');
  if (!ls) return;
  ls.style.opacity = '0';
  ls.style.transition = 'opacity 0.6s ease';
  setTimeout(() => ls.style.display = 'none', 650);
}

// ─── GEOLOCATION ─────────────────────────────────────────────────
function initGeolocation() {
  if (!navigator.geolocation) {
    // Default to Bardhaman, West Bengal
    currentLat = 23.23; currentLon = 87.85;
    onLocationReady('Bardhaman, West Bengal');
    return;
  }
  navigator.geolocation.getCurrentPosition(
    pos => {
      currentLat = pos.coords.latitude;
      currentLon = pos.coords.longitude;
      reverseGeocode(currentLat, currentLon);
    },
    () => {
      currentLat = 23.23; currentLon = 87.85;
      onLocationReady('Bardhaman, West Bengal');
    },
    { timeout: 8000 }
  );
}

function reverseGeocode(lat, lon) {
  fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`)
    .then(r => r.json())
    .then(d => {
      const city = d.address.city || d.address.town || d.address.village || d.address.county || 'Your Location';
      const state = d.address.state || '';
      onLocationReady(`${city}${state ? ', ' + state : ''}`);
    })
    .catch(() => onLocationReady('Your Location'));
}

function onLocationReady(name) {
  const el = document.getElementById('locationNameEl');
  if (el) el.textContent = name;
  fetchWeather(currentLat, currentLon);
  initMap(currentLat, currentLon);
  runPrediction();
}

// ─── WEATHER ─────────────────────────────────────────────────────
function fetchWeather(lat, lon) {
  // Show loading shimmer
  document.querySelectorAll('.wc-val').forEach(el => {
    el.textContent = '...';
  });

  fetch(`${WEATHER_API}?lat=${lat}&lon=${lon}&appid=${WEATHER_API_KEY}&units=metric`)
    .then(r => {
      if (!r.ok) throw new Error('Weather API error');
      return r.json();
    })
    .then(d => renderWeather(d))
    .catch(() => {
      // Inject mock data so UI isn't empty
      renderWeather(mockWeatherData(lat));
    });
}

function mockWeatherData(lat) {
  // Realistic mock for demo
  const isHot = lat < 25;
  return {
    main: { temp: isHot ? 38 : 29, humidity: 72, pressure: 1008 },
    wind: { speed: 12 },
    visibility: 8000,
    weather: [{ main: 'Clouds', description: 'partly cloudy', icon: '04d' }],
    rain: { '1h': 0 }
  };
}

function renderWeather(d) {
  setWCard('temp', Math.round(d.main.temp), d.main.temp, 50);
  setWCard('humidity', d.main.humidity, d.main.humidity, 100);
  setWCard('wind', Math.round((d.wind?.speed || 0) * 3.6), (d.wind?.speed || 0) * 3.6, 120);
  setWCard('pressure', d.main.pressure, ((d.main.pressure - 950) / 100) * 100, 100);
  setWCard('visibility', ((d.visibility || 10000) / 1000).toFixed(1), (d.visibility || 10000) / 100, 100);
  setWCard('rain', d.rain ? Math.round((d.rain['1h'] || 0) * 100) : 0, d.rain ? (d.rain['1h'] || 0) * 100 : 0, 100);
  setWCard('uv', '—', 55, 100); // OWM UV needs separate call; show placeholder
  // Condition
  const condEl = document.getElementById('wVal-condition');
  if (condEl) condEl.textContent = d.weather[0]?.main || 'Clear';
  const iconEl = document.getElementById('wcIcon-condition');
  if (iconEl) iconEl.textContent = conditionEmoji(d.weather[0]?.main || '');
}

function setWCard(key, displayVal, numVal, max) {
  const valEl = document.getElementById(`wVal-${key}`);
  const barEl = document.getElementById(`wbar-${key}`);
  if (valEl) valEl.textContent = displayVal;
  if (barEl) {
    const pct = Math.min(100, Math.max(0, (numVal / max) * 100));
    barEl.style.width = pct + '%';
  }
}

function conditionEmoji(main) {
  const map = { Clear: '☀', Clouds: '🌤', Rain: '🌧', Drizzle: '🌦', Thunderstorm: '⛈', Snow: '❄', Mist: '🌫', Fog: '🌫', Haze: '🌫' };
  return map[main] || '🌤';
}

// ─── PREDICTION ───────────────────────────────────────────────────
async function runPrediction() {
  if (!currentLat) { showToast('Detecting your location...', 'info'); return; }

  const spinIcon = document.getElementById('spinIcon');
  if (spinIcon) spinIcon.classList.add('spinning');

  try {
    const res = await fetch(`${BASE_URL}/api/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat: currentLat, lon: currentLon })
    });
    if (!res.ok) throw new Error('Prediction API error');
    const data = await res.json();
    renderPrediction(data);
  } catch (e) {
    // Fallback mock — shows as low risk clear
    renderPrediction({
      flood_probability: 18, cyclone_probability: 8, heatwave_probability: 30,
      predicted_disaster: 'None', confidence: 30, alert: false,
      location: { lat: currentLat, lon: currentLon }
    });
    showToast('Using demo data (backend offline)', 'info');
  } finally {
    if (spinIcon) spinIcon.classList.remove('spinning');
  }
}

function renderPrediction(data) {
  // Probability bars
  animateProbBar('floodBar', 'floodPct', data.flood_probability);
  animateProbBar('cycloneBar', 'cyclonePct', data.cyclone_probability);
  animateProbBar('heatBar', 'heatPct', data.heatwave_probability);

  if (data.alert) {
    const dtype = (data.predicted_disaster || 'flood').toLowerCase();
    currentDisaster = dtype;
    isSimulating = false;
    applyDisasterUI(dtype, data.confidence);
    fetchMitigation(dtype, data.confidence);
  } else {
    currentDisaster = null;
    isSimulating = false;
    applyAllClearUI();
  }
}

function animateProbBar(barId, pctId, value) {
  const bar = document.getElementById(barId);
  const pct = document.getElementById(pctId);
  if (!bar || !pct) return;
  let current = 0;
  const step = value / 40;
  const interval = setInterval(() => {
    current = Math.min(current + step, value);
    bar.style.width = current + '%';
    pct.textContent = Math.round(current) + '%';
    if (current >= value) clearInterval(interval);
  }, 20);
}

// ─── DISASTER / CLEAR UI ─────────────────────────────────────────
function applyDisasterUI(dtype, confidence) {
  const card = document.getElementById('statusCard');
  const icon = document.getElementById('statusIcon');
  const badge = document.getElementById('statusBadge');
  const title = document.getElementById('statusTitle');
  const desc = document.getElementById('statusDesc');
  const meta = document.getElementById('scMeta');

  const configs = {
    flood: { icon: '🌊', badge: t('flood_alert'), title: t('flood_alert'), desc: t('flood_desc'), cls: 'disaster-flood' },
    cyclone: { icon: '🌀', badge: t('cyclone_alert'), title: t('cyclone_alert'), desc: t('cyclone_desc'), cls: 'disaster-cyclone' },
    heatwave: { icon: '🌡', badge: t('heat_alert'), title: t('heat_alert'), desc: t('heat_desc'), cls: 'disaster-heat' },
  };
  const cfg = configs[dtype] || configs.flood;

  card.className = 'status-card ' + cfg.cls;
  icon.textContent = cfg.icon;
  badge.textContent = cfg.badge;
  title.textContent = cfg.title;
  desc.textContent = cfg.desc;
  if (meta) meta.innerHTML = `<span class="sc-meta-chip">Confidence: ${confidence}%</span>`;

  // Map update
  updateMapForDisaster(dtype);
  const mapMsg = document.getElementById('mapStatusMsg');
  if (mapMsg) mapMsg.textContent = t('map_danger');

  // Radar color
  const radar = document.getElementById('radarContainer');
  if (radar) {
    radar.style.setProperty('--rad-color', dtype === 'flood' ? '#00aaff' : dtype === 'cyclone' ? '#cc44ff' : '#ff6600');
  }
}

function applyAllClearUI() {
  const card = document.getElementById('statusCard');
  const icon = document.getElementById('statusIcon');
  const badge = document.getElementById('statusBadge');
  const title = document.getElementById('statusTitle');
  const desc = document.getElementById('statusDesc');
  const meta = document.getElementById('scMeta');

  card.className = 'status-card';
  icon.textContent = '🛡';
  badge.textContent = t('badge_clear');
  badge.setAttribute('data-i18n', 'badge_clear');
  title.textContent = t('status_safe_title');
  desc.textContent = t('status_safe_desc');
  if (meta) meta.innerHTML = '';

  updateMapSafe();
  const mapMsg = document.getElementById('mapStatusMsg');
  if (mapMsg) mapMsg.textContent = t('map_safe');

  // Mitigation hide
  document.getElementById('mitGrid').style.display = 'none';
  document.getElementById('severityRow').style.display = 'none';
  document.getElementById('mitPlaceholder').style.display = 'flex';
}

// ─── SIMULATION ───────────────────────────────────────────────────
async function simulateDisaster(dtype) {
  currentDisaster = dtype;
  isSimulating = true;

  const probs = {
    flood: { flood_probability: 84, cyclone_probability: 20, heatwave_probability: 15, confidence: 84 },
    cyclone: { flood_probability: 22, cyclone_probability: 91, heatwave_probability: 10, confidence: 91 },
    heatwave: { flood_probability: 10, cyclone_probability: 8, heatwave_probability: 88, confidence: 88 },
  };
  const p = probs[dtype];

  animateProbBar('floodBar', 'floodPct', p.flood_probability);
  animateProbBar('cycloneBar', 'cyclonePct', p.cyclone_probability);
  animateProbBar('heatBar', 'heatPct', p.heatwave_probability);

  applyDisasterUI(dtype, p.confidence);
  scrollToSection('predictionSection');

  await fetchMitigation(dtype, p.confidence);

  const label = { flood: '🌊 Flood', cyclone: '🌀 Cyclone', heatwave: '🌡 Heatwave' }[dtype];
  showToast(`${label} simulation activated`, 'warn');
}

function resetSimulation() {
  currentDisaster = null;
  isSimulating = false;

  animateProbBar('floodBar', 'floodPct', 0);
  animateProbBar('cycloneBar', 'cyclonePct', 0);
  animateProbBar('heatBar', 'heatPct', 0);

  applyAllClearUI();
  showToast('Simulation reset — All Clear ✅', 'success');
  scrollToSection('predictionSection');
}

// ─── MITIGATION ───────────────────────────────────────────────────
async function fetchMitigation(dtype, probability) {
  try {
    const res = await fetch(`${BASE_URL}/api/mitigation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_type: currentUserType,
        disaster: dtype,
        probability: Math.round(probability)
      })
    });
    if (!res.ok) throw new Error('Mitigation API error');
    const data = await res.json();
    renderMitigation(data);
  } catch (e) {
    renderMitigation(mockMitigation(dtype, currentUserType));
  }
}

function mockMitigation(dtype, userType) {
  const base = {
    flood: {
      severity: 'High',
      things_to_do: [
        'Move to higher ground immediately',
        'Turn off gas and electricity at main switches',
        'Store drinking water in clean containers',
        'Keep emergency documents in waterproof bag',
        'Follow official evacuation orders promptly'
      ],
      things_not_to_do: [
        'Do not walk through moving floodwater',
        'Do not touch electrical equipment if wet',
        'Do not ignore official warnings',
        'Do not drive through flooded roads',
        'Do not return home until authorities say it\'s safe'
      ],
      emergency_kit: ['Flashlight & batteries', 'First aid kit', 'Bottled water (3-day supply)', 'Important documents', 'Warm clothing & blankets']
    },
    cyclone: {
      severity: 'Critical',
      things_to_do: [
        'Seek shelter in a strong, permanent building',
        'Stay away from windows and glass doors',
        'Stock food and water for 72 hours',
        'Keep battery-powered radio for alerts',
        'Secure loose outdoor furniture and objects'
      ],
      things_not_to_do: [
        'Do not go outside during the storm',
        'Do not shelter under trees',
        'Do not use candles near gas leaks',
        'Do not drive during the cyclone',
        'Do not enter damaged buildings'
      ],
      emergency_kit: ['Battery radio', 'Water & food for 3 days', 'First aid kit', 'Torch with extra batteries', 'Cash & important documents']
    },
    heatwave: {
      severity: 'Medium',
      things_to_do: [
        'Stay indoors during peak heat hours (11am-4pm)',
        'Drink water frequently, at least 8-10 glasses daily',
        'Wear loose, light-colored cotton clothing',
        'Use wet cloth on neck and wrists to cool down',
        'Check on elderly neighbors and vulnerable people'
      ],
      things_not_to_do: [
        'Do not go out without head cover in direct sun',
        'Do not drink alcohol or caffeine-heavy beverages',
        'Do not leave children or pets in parked vehicles',
        'Do not exercise outdoors during peak heat',
        'Do not eat heavy, hot meals during the day'
      ],
      emergency_kit: ['ORS packets', 'Cooling towels', 'Sunscreen & hat', 'Plenty of water', 'Fan / cooling device']
    }
  };

  if (userType === 'farmer' && dtype === 'flood') {
    base.flood.things_to_do[0] = 'Move livestock to higher ground immediately';
    base.flood.things_to_do[1] = 'Harvest standing crops urgently if safe to do so';
  }
  if (userType === 'elderly') {
    base[dtype].things_to_do.push('Contact family members and inform them of your location');
  }

  return base[dtype] || base.flood;
}

async function renderMitigation(data) {
  document.getElementById('mitPlaceholder').style.display = 'none';

  const severityRow = document.getElementById('severityRow');
  const chip = document.getElementById('severityChip');
  severityRow.style.display = 'flex';
  chip.textContent = data.severity;
  chip.className = 'sev-chip sev-' + (data.severity || 'Medium').toLowerCase();

  data.things_to_do =
    await translateContent(
      data.things_to_do
    );

  data.things_not_to_do =
    await translateContent(
      data.things_not_to_do
    );

  data.emergency_kit =
    await translateContent(
      data.emergency_kit
    );

  populateList(
    'doList',
    data.things_to_do
  );

  populateList(
    'dontList',
    data.things_not_to_do
  );

  populateList(
    'kitList',
    data.emergency_kit
  );

  document.getElementById('mitGrid').style.display = 'grid';
  scrollToSection('mitigationSection');
}
async function translateContent(texts) {

  if (currentLang === "en")
    return texts;

  const translated = [];

  for (const text of texts) {

    try {

      const res = await fetch(
        "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl="
        + langMap[currentLang]
        + "&dt=t&q="
        + encodeURIComponent(text)
      );

      const data = await res.json();

      translated.push(data[0][0][0]);

    } catch (error) {

      console.log(
        "Translation failed:",
        error
      );

      translated.push(text);

    }

  }

  return translated;
}

function populateList(listId, items) {
  const ul = document.getElementById(listId);
  if (!ul) return;
  ul.innerHTML = '';
  (items || []).forEach(item => {
    const li = document.createElement('li');
    li.textContent = item;
    li.style.animationDelay = Math.random() * 0.3 + 's';
    ul.appendChild(li);
  });
}

// ─── SPEECH SYNTHESIS ────────────────────────────────────────────
function speakList(listId) {
  const ul = document.getElementById(listId);
  if (!ul) return;
  const items = Array.from(ul.querySelectorAll('li')).map(li => li.textContent);
  speakText(items.join('. '));
}

function speakBubble(btn) {
  const bubble = btn.closest('.cm-bubble');
  const p = bubble ? bubble.querySelector('p') : null;
  if (p) speakText(p.textContent);
}

function speakText(text) {
  if (!speechSynth) return;
  speechSynth.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = speechLangCodes[currentLang] || 'en-IN';
  utt.rate = 0.9;
  utt.pitch = 1;
  speechSynth.speak(utt);
}

// ─── VOICE INPUT ──────────────────────────────────────────────────
function toggleVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showToast('Voice input not supported in your browser', 'warn');
    return;
  }

  if (isListening) {
    stopVoiceInput();
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = speechLangCodes[currentLang] || 'en-IN';
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    isListening = true;
    document.getElementById('micBtn').classList.add('active-mic');
    document.getElementById('voiceBar').style.display = 'flex';
  };

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    document.getElementById('chatInput').value = transcript;
    stopVoiceInput();
    sendChatMessage();
  };

  recognition.onerror = () => { stopVoiceInput(); showToast('Voice recognition error. Try again.', 'warn'); };
  recognition.onend = () => stopVoiceInput();
  recognition.start();
}

function stopVoiceInput() {
  isListening = false;
  if (recognition) recognition.stop();
  const micBtn = document.getElementById('micBtn');
  if (micBtn) micBtn.classList.remove('active-mic');
  const vb = document.getElementById('voiceBar');
  if (vb) vb.style.display = 'none';
}

// ─── CHAT / VOICE MODAL ───────────────────────────────────────────
function openVoiceModal() {
  document.getElementById('voiceModal').classList.add('open');
  setTimeout(() => document.getElementById('chatInput')?.focus(), 300);
}

function closeVoiceModal() {
  document.getElementById('voiceModal').classList.remove('open');
  stopVoiceInput();
}

function handleOverlayClick(e) {
  if (e.target.id === 'voiceModal') closeVoiceModal();
}

async function sendChatMessage() {
  const input = document.getElementById('chatInput');
  const question = input.value.trim();
  if (!question) return;
  input.value = '';

  addChatMsg(question, 'user');

  // Typing indicator
  const typingId = 'typing-' + Date.now();
  addTypingIndicator(typingId);

  try {
    const res = await fetch(`${BASE_URL}/api/voice-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: question,
        user_type: currentUserType,
        location: document.getElementById('locationNameEl')?.textContent || ''
      })
    });
    if (!res.ok) throw new Error('Chat API error');
    const data = await res.json();
    removeTypingIndicator(typingId);
    addChatMsg(data.answer, 'ai');
  } catch (e) {
    removeTypingIndicator(typingId);
    const fallback = generateFallbackResponse(question);
    addChatMsg(fallback, 'ai');
  }
}

function generateFallbackResponse(question) {
  const q = question.toLowerCase();
  if (q.includes('flood') || q.includes('বন্যা') || q.includes('बाढ़'))
    return 'During a flood: move to higher ground immediately, avoid walking through floodwater, and follow official evacuation orders. Keep emergency kit ready.';
  if (q.includes('cyclone') || q.includes('ঘূর্ণিঝড়') || q.includes('चक्रवात'))
    return 'During a cyclone: seek shelter in a strong building, stay away from windows, stock food & water for 72 hours, and monitor official alerts.';
  if (q.includes('heat') || q.includes('তাপ') || q.includes('গরম') || q.includes('गर्मी'))
    return 'During a heatwave: stay indoors between 11am-4pm, drink plenty of water, wear light clothing, and avoid outdoor activity.';
  return 'APADAMITRA AI monitors floods, cyclones, and heatwaves. Ask me about disaster preparedness, safety tips, or what to do during an emergency in your area.';
}

function addChatMsg(text, role) {
  const win = document.getElementById('chatWindow');
  const div = document.createElement('div');
  div.className = `chat-msg ${role === 'user' ? 'user-msg' : 'ai-msg'}`;

  if (role === 'ai') {
    div.innerHTML = `
      <div class="cm-av">🤖</div>
      <div class="cm-bubble">
        <p>${text}</p>
        <button class="bubble-speak" onclick="speakBubble(this)">🔊</button>
      </div>`;
  } else {
    div.innerHTML = `<div class="cm-bubble user-bubble"><p>${text}</p></div>`;
  }

  win.appendChild(div);
  win.scrollTop = win.scrollHeight;
}

function addTypingIndicator(id) {
  const win = document.getElementById('chatWindow');
  const div = document.createElement('div');
  div.className = 'chat-msg ai-msg';
  div.id = id;
  div.innerHTML = `<div class="cm-av">🤖</div><div class="cm-bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>`;
  win.appendChild(div);
  win.scrollTop = win.scrollHeight;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ─── MAP ──────────────────────────────────────────────────────────
function initMap(lat, lon) {
  if (map) { map.remove(); map = null; }
  map = L.map('safetyMap', { zoomControl: true, attributionControl: true }).setView([lat, lon], 11);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© CartoDB',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);

  // User marker
  userMarker = L.circleMarker([lat, lon], {
    radius: 10, fillColor: '#00c8ff', color: '#fff',
    weight: 2, opacity: 1, fillOpacity: 0.9
  }).addTo(map).bindPopup('📍 Your Location').openPopup();

  drawSafeZone(lat, lon);
}

function drawSafeZone(lat, lon) {
  clearMapLayers();
  const safeCircle = L.circle([lat, lon], {
    radius: 15000, color: '#00ff88', fillColor: '#00ff88',
    fillOpacity: 0.08, weight: 1.5, dashArray: '6 4'
  }).addTo(map);
  mapLayers.safe.push(safeCircle);
}

function updateMapForDisaster(dtype) {
  if (!map || !currentLat) return;
  clearMapLayers();

  const lat = currentLat; const lon = currentLon;
  const dangerColor = dtype === 'cyclone' ? '#cc44ff' : dtype === 'heatwave' ? '#ff6600' : '#ff3366';
  const warnColor = '#ffaa00';

  // Danger zone (offset slightly)
  const dCircle = L.circle([lat + 0.05, lon - 0.04], {
    radius: 8000, color: dangerColor, fillColor: dangerColor,
    fillOpacity: 0.15, weight: 2
  }).addTo(map).bindPopup(`🚨 ${dtype.charAt(0).toUpperCase() + dtype.slice(1)} Danger Zone`);
  mapLayers.danger.push(dCircle);

  // Warning zone
  const wCircle = L.circle([lat - 0.03, lon + 0.05], {
    radius: 6000, color: warnColor, fillColor: warnColor,
    fillOpacity: 0.1, weight: 2
  }).addTo(map).bindPopup('⚠ Warning Zone');
  mapLayers.warn.push(wCircle);

  // Safe zone (smaller)
  const sCircle = L.circle([lat + 0.08, lon + 0.1], {
    radius: 5000, color: '#00ff88', fillColor: '#00ff88',
    fillOpacity: 0.1, weight: 1.5
  }).addTo(map).bindPopup('✅ Evacuation Safe Zone');
  mapLayers.safe.push(sCircle);

  // Animated pulse marker at danger center
  const pulseIcon = L.divIcon({
    className: '',
    html: `<div style="width:20px;height:20px;border-radius:50%;background:${dangerColor};opacity:0.9;box-shadow:0 0 0 0 ${dangerColor};animation:mapPulse 1.2s infinite;"></div>`,
    iconSize: [20, 20], iconAnchor: [10, 10]
  });
  const pulse = L.marker([lat + 0.05, lon - 0.04], { icon: pulseIcon }).addTo(map);
  mapLayers.danger.push(pulse);

  map.setView([lat, lon], 10, { animate: true });
}

function updateMapSafe() {
  if (!map || !currentLat) return;
  drawSafeZone(currentLat, currentLon);
  map.setView([currentLat, currentLon], 11, { animate: true });
}

function clearMapLayers() {
  [...mapLayers.safe, ...mapLayers.warn, ...mapLayers.danger].forEach(l => {
    if (map && l) map.removeLayer(l);
  });
  mapLayers = { safe: [], warn: [], danger: [] };
}

// ─── MOBILE NAV ───────────────────────────────────────────────────
function toggleMobileNav() {
  const nav = document.getElementById('mobileNav');
  const btn = document.getElementById('hamburgerBtn');
  if (!nav) return;
  const open = nav.classList.toggle('open');
  btn.classList.toggle('open', open);
}

// ─── HEADER SCROLL EFFECT ────────────────────────────────────────
function initHeaderScroll() {
  const header = document.getElementById('siteHeader');
  if (!header) return;
  window.addEventListener('scroll', () => {
    header.classList.toggle('scrolled', window.scrollY > 60);
  }, { passive: true });
}

// ─── INTERSECTION OBSERVER (section entry animations) ────────────
function initSectionObserver() {
  const sections = document.querySelectorAll('.page-section');
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('section-visible');
      }
    });
  }, { threshold: 0.08 });
  sections.forEach(s => obs.observe(s));
}

// ─── ADD DYNAMIC STYLES (typing dots, toast, map pulse) ──────────
function injectDynamicStyles() {
  const style = document.createElement('style');
  style.textContent = `
    /* Toast */
    .toast-wrap { position:fixed; bottom:90px; right:20px; z-index:9999; display:flex; flex-direction:column; gap:8px; }
    .toast { background:rgba(15,25,50,0.95); color:#e0e8ff; border:1px solid rgba(0,200,255,0.3);
      border-radius:12px; padding:12px 18px; font-size:0.85rem; font-family:'Exo 2',sans-serif;
      backdrop-filter:blur(20px); opacity:0; transform:translateX(30px);
      transition:all 0.35s ease; max-width:280px; box-shadow:0 4px 20px rgba(0,0,0,0.4); }
    .toast.show { opacity:1; transform:translateX(0); }
    .toast-success { border-color:rgba(0,255,136,0.4); }
    .toast-warn    { border-color:rgba(255,170,0,0.4);  }
    .toast-error   { border-color:rgba(255,50,80,0.4);  }

    /* Typing dots */
    .typing-dots { display:flex; gap:5px; align-items:center; padding:4px 0; }
    .typing-dots span { width:8px; height:8px; border-radius:50%; background:#00c8ff;
      animation:typingBounce 1.2s infinite ease-in-out; }
    .typing-dots span:nth-child(2) { animation-delay:0.2s; }
    .typing-dots span:nth-child(3) { animation-delay:0.4s; }
    @keyframes typingBounce { 0%,80%,100%{transform:scale(0.7);opacity:0.5} 40%{transform:scale(1);opacity:1} }

    /* Active mic */
    .active-mic { background:rgba(255,50,80,0.3) !important; border-color:rgba(255,50,80,0.6) !important; }

    /* Spin */
    .spinning { animation:spin 0.8s linear infinite; display:inline-block; }
    @keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

    /* Map pulse */
    @keyframes mapPulse {
      0%   { box-shadow:0 0 0 0 rgba(255,50,80,0.7); }
      70%  { box-shadow:0 0 0 16px rgba(255,50,80,0); }
      100% { box-shadow:0 0 0 0 rgba(255,50,80,0); }
    }

    /* Severity chips */
    .sev-low      { background:rgba(0,255,136,0.2); color:#00ff88; border-color:rgba(0,255,136,0.4); }
    .sev-medium   { background:rgba(255,170,0,0.2); color:#ffaa00; border-color:rgba(255,170,0,0.4); }
    .sev-high     { background:rgba(255,80,0,0.2);  color:#ff5000; border-color:rgba(255,80,0,0.4); }
    .sev-critical { background:rgba(255,0,60,0.2);  color:#ff003c; border-color:rgba(255,0,60,0.4); }

    /* User chat bubble */
    .user-bubble { background:rgba(0,200,255,0.15); border:1px solid rgba(0,200,255,0.3); margin-left:auto; }
    .user-msg    { flex-direction:row-reverse; }

    /* Status card disaster states */
    .disaster-flood   { background:linear-gradient(135deg,rgba(0,100,255,0.15),rgba(0,30,80,0.4)); border-color:rgba(0,100,255,0.4); }
    .disaster-cyclone { background:linear-gradient(135deg,rgba(150,0,255,0.15),rgba(40,0,80,0.4)); border-color:rgba(150,0,255,0.4); }
    .disaster-heat    { background:linear-gradient(135deg,rgba(255,100,0,0.15),rgba(80,20,0,0.4));  border-color:rgba(255,100,0,0.4); }

    .sc-meta-chip { background:rgba(0,200,255,0.1); border:1px solid rgba(0,200,255,0.3);
      border-radius:20px; padding:4px 14px; font-size:0.8rem; color:#00c8ff; }

    /* Section entry */
    .page-section { opacity:0; transform:translateY(24px); transition:opacity 0.6s ease, transform 0.6s ease; }
    .section-visible { opacity:1; transform:translateY(0); }

    /* Modal open */
    .modal-bg.open { display:flex !important; }
  `;
  document.head.appendChild(style);
}

// ─── INIT ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  injectDynamicStyles();
  initHeaderScroll();
  initSectionObserver();
  applyI18n();

  // Hide loading screen after 2.2s
  setTimeout(hideLoadingScreen, 2200);

  // Start geolocation & data pipeline
  initGeolocation();

  // Auto-refresh prediction every 5 minutes
  setInterval(() => {
    if (currentLat && !isSimulating) runPrediction();
  }, 5 * 60 * 1000);
});