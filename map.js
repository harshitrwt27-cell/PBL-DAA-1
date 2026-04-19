// Leaflet Map Configuration
let map;
let markers = [];
let routeLayer;

// Initialize map
function initMap() {
    // Center on Delhi
    map = L.map('map').setView([28.6139, 77.2090], 11);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(map);

    // Add bus stop markers
    addBusStopMarkers();
}

// Bus stop coordinates (Delhi locations)
const busStops = {
    'Connaught Place': [28.6304, 77.2177],
    'India Gate': [28.6129, 77.2295],
    'Karol Bagh': [28.6517, 77.1892],
    'Rajiv Chowk': [28.6304, 77.2177], // Metro station near CP
    'Lajpat Nagar': [28.5783, 77.2400],
    'Nehru Place': [28.5494, 77.2500],
    'Punjabi Bagh': [28.6743, 77.1315]
};

function addBusStopMarkers() {
    Object.entries(busStops).forEach(([name, coords]) => {
        const marker = L.marker(coords)
            .addTo(map)
            .bindPopup(`<b>${name}</b><br>Bus Stop`)
            .bindTooltip(name, {permanent: false, direction: 'top'});

        markers.push(marker);
    });
}

// Draw route on map
function drawRoute(path) {
    // Clear previous route
    if (routeLayer) {
        map.removeLayer(routeLayer);
    }

    if (!path || path.length < 2) return;

    const routeCoords = path.map(stop => busStops[stop]);
    routeLayer = L.polyline(routeCoords, {
        color: '#667eea',
        weight: 4,
        opacity: 0.8
    }).addTo(map);

    // Fit map to route
    map.fitBounds(routeLayer.getBounds(), {padding: [20, 20]});

    // Add start and end markers
    const startIcon = L.divIcon({
        html: '<div style="background: #4CAF50; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>',
        className: 'custom-marker',
        iconSize: [20, 20]
    });

    const endIcon = L.divIcon({
        html: '<div style="background: #f44336; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>',
        className: 'custom-marker',
        iconSize: [20, 20]
    });

    L.marker(routeCoords[0], {icon: startIcon})
        .addTo(map)
        .bindPopup('<b>START</b><br>' + path[0]);

    L.marker(routeCoords[routeCoords.length - 1], {icon: endIcon})
        .addTo(map)
        .bindPopup('<b>END</b><br>' + path[path.length - 1]);
}

// Initialize map when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('map')) {
        initMap();
    }
});