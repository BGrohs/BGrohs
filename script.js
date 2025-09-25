const map = L.map('map', {
  zoomControl: false,
}).setView([20, 0], 2);

L.control.zoom({ position: 'topright' }).addTo(map);

const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
});

tileLayer.addTo(map);

let startMarker = null;
let pois = [];
let drivingRoute = null;
let walkingRoute = null;
let flightLayer = null;
let pendingMapMode = null;

const startInput = document.getElementById('start-address');
const startSearchBtn = document.getElementById('start-search');
const startMapBtn = document.getElementById('use-map-start');
const poiInput = document.getElementById('poi-address');
const poiSearchBtn = document.getElementById('poi-search');
const poiMapBtn = document.getElementById('use-map-poi');
const poiList = document.getElementById('poi-list');
const mapHint = document.getElementById('map-hint');
const drivingToggle = document.getElementById('toggle-driving');
const walkingToggle = document.getElementById('toggle-walking');
const flightToggle = document.getElementById('toggle-flight');
const clearPoisBtn = document.getElementById('clear-pois');

const geocoder = L.Control.Geocoder.nominatim();

function setMapHint(message = '') {
  mapHint.textContent = message;
}

function setStart(latlng, label) {
  if (startMarker) {
    startMarker.setLatLng(latlng);
  } else {
    startMarker = L.marker(latlng, { title: label }).addTo(map);
  }
  startMarker.bindPopup(`<strong>Start:</strong> ${label}`).openPopup();
  fitMapToPoints();
  updateRoutes();
}

function addPoi(latlng, label) {
  const marker = L.marker(latlng, { title: label }).addTo(map);
  marker.bindPopup(`<strong>POI:</strong> ${label}`);
  const poi = {
    id: generateId(),
    marker,
    label,
  };
  pois.push(poi);
  renderPoiList();
  fitMapToPoints();
  updateRoutes();
}

function removePoi(id) {
  const index = pois.findIndex((poi) => poi.id === id);
  if (index === -1) return;
  const [removed] = pois.splice(index, 1);
  map.removeLayer(removed.marker);
  renderPoiList();
  fitMapToPoints();
  updateRoutes();
}

function clearPois() {
  pois.forEach((poi) => map.removeLayer(poi.marker));
  pois = [];
  renderPoiList();
  updateRoutes();
}

function renderPoiList() {
  poiList.innerHTML = '';
  if (pois.length === 0) {
    const empty = document.createElement('li');
    empty.textContent = 'No points added yet.';
    empty.className = 'hint';
    poiList.appendChild(empty);
    return;
  }
  pois.forEach((poi, index) => {
    const item = document.createElement('li');
    item.className = 'poi-item';
    const label = document.createElement('span');
    label.textContent = `${index + 1}. ${poi.label}`;
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.textContent = 'Remove';
    removeBtn.addEventListener('click', () => removePoi(poi.id));
    item.append(label, removeBtn);
    poiList.appendChild(item);
  });
}

function getWaypoints() {
  if (!startMarker || pois.length === 0) {
    return null;
  }
  const startPoint = startMarker.getLatLng();
  const poiPoints = pois.map((poi) => poi.marker.getLatLng());
  return [startPoint, ...poiPoints];
}

function fitMapToPoints() {
  const points = [];
  if (startMarker) {
    points.push(startMarker.getLatLng());
  }
  pois.forEach((poi) => points.push(poi.marker.getLatLng()));
  if (points.length === 0) return;
  if (points.length === 1) {
    map.setView(points[0], 13);
    return;
  }
  const bounds = L.latLngBounds(points);
  map.fitBounds(bounds.pad(0.2));
}

function teardownRoute(control) {
  if (!control) return null;
  map.removeControl(control);
  return null;
}

function updateRoutes() {
  const waypoints = getWaypoints();
  if (!waypoints) {
    drivingRoute = teardownRoute(drivingRoute);
    walkingRoute = teardownRoute(walkingRoute);
    if (flightLayer) {
      map.removeLayer(flightLayer);
      flightLayer = null;
    }
    return;
  }

  if (drivingToggle.checked) {
    if (!drivingRoute) {
      drivingRoute = createRoutingControl('car', '#1d4ed8', waypoints);
    }
    drivingRoute.getPlan().setWaypoints(waypoints);
  } else {
    drivingRoute = teardownRoute(drivingRoute);
  }

  if (walkingToggle.checked) {
    if (!walkingRoute) {
      walkingRoute = createRoutingControl('foot', '#10b981', waypoints);
    }
    walkingRoute.getPlan().setWaypoints(waypoints);
  } else {
    walkingRoute = teardownRoute(walkingRoute);
  }

  if (flightToggle.checked) {
    drawFlightPath(waypoints);
  } else if (flightLayer) {
    map.removeLayer(flightLayer);
    flightLayer = null;
  }
}

function createRoutingControl(profile, color, waypoints) {
  const control = L.Routing.control({
    waypoints: waypoints || [],
    router: L.Routing.osrmv1({
      serviceUrl: 'https://router.project-osrm.org/route/v1',
      profile,
    }),
    lineOptions: {
      styles: [
        {
          color,
          weight: 6,
          opacity: 0.8,
        },
      ],
    },
    fitSelectedRoutes: false,
    show: false,
    addWaypoints: false,
    routeWhileDragging: false,
    draggableWaypoints: false,
    createMarker: () => null,
  }).addTo(map);

  control.on('routingerror', (event) => {
    console.error('Routing error', event);
  });

  return control;
}

function drawFlightPath(waypoints) {
  if (flightLayer) {
    map.removeLayer(flightLayer);
  }
  if (!waypoints || waypoints.length < 2) {
    flightLayer = null;
    return;
  }
  const segments = [];
  for (let i = 0; i < waypoints.length - 1; i += 1) {
    segments.push([waypoints[i], waypoints[i + 1]]);
  }
  flightLayer = L.geodesic(segments, {
    weight: 4,
    opacity: 0.6,
    color: '#f97316',
    steps: 100,
  }).addTo(map);
}

function generateId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function geocodeSearch(query) {
  if (!query) return null;
  return new Promise((resolve) => {
    geocoder.geocode(query, (results) => {
      resolve(results && results.length ? results[0] : null);
    });
  });
}

async function handleStartSearch() {
  const query = startInput.value.trim();
  if (!query) return;
  setMapHint('Searching for start location...');
  const result = await geocodeSearch(query);
  setMapHint('');
  if (!result) {
    alert('No results found for the start location.');
    return;
  }
  setStart(result.center, result.name || result.html || query);
}

async function handlePoiSearch() {
  const query = poiInput.value.trim();
  if (!query) return;
  setMapHint('Searching for point of interest...');
  const result = await geocodeSearch(query);
  setMapHint('');
  if (!result) {
    alert('No results found for that point of interest.');
    return;
  }
  addPoi(result.center, result.name || result.html || query);
  poiInput.value = '';
}

function enableMapSelection(mode) {
  pendingMapMode = mode;
  if (mode === 'start') {
    setMapHint('Click on the map to choose the start location.');
  } else {
    setMapHint('Click on the map to add a point of interest.');
  }
}

map.on('click', (event) => {
  if (!pendingMapMode) return;
  const label = `${pendingMapMode === 'start' ? 'Start' : 'POI'} (${event.latlng.lat.toFixed(
    4
  )}, ${event.latlng.lng.toFixed(4)})`;
  if (pendingMapMode === 'start') {
    setStart(event.latlng, label);
  } else {
    addPoi(event.latlng, label);
  }
  pendingMapMode = null;
  setMapHint('');
});

startSearchBtn.addEventListener('click', handleStartSearch);
startInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    handleStartSearch();
  }
});

poiSearchBtn.addEventListener('click', handlePoiSearch);
poiInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    handlePoiSearch();
  }
});

startMapBtn.addEventListener('click', () => enableMapSelection('start'));
poiMapBtn.addEventListener('click', () => enableMapSelection('poi'));

drivingToggle.addEventListener('change', updateRoutes);
walkingToggle.addEventListener('change', updateRoutes);
flightToggle.addEventListener('change', updateRoutes);
clearPoisBtn.addEventListener('click', clearPois);

renderPoiList();
setMapHint('Search above or use the map to start planning.');
