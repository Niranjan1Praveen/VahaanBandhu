document.addEventListener('DOMContentLoaded', function() {
    // Variables to store map elements
    let map;
    let truckMarkers = {};
    let mandisLayer;
    let updatesActive = true;
    let updateInterval;
    const updateFrequency = 5000; // 5 seconds
    
    // Get DOM elements
    const truckListElement = document.getElementById('truck-list');
    const lastUpdatedElement = document.getElementById('last-updated');
    const toggleUpdatesBtn = document.getElementById('toggle-updates');
    const updateStatusBadge = document.getElementById('update-status');
    
    // Initialize map from the Folium-generated one
    function initializeMap() {
        // Find the Leaflet map instance created by Folium
        // This may require waiting for the map to load
        let attempts = 0;
        let initMapInterval = setInterval(() => {
            // Look for Leaflet map container
            const mapContainer = document.querySelector('.leaflet-container');
            if (mapContainer) {
                // Find the map object
                map = Object.values(mapContainer).find(prop => prop && prop._container === mapContainer);
                if (map) {
                    clearInterval(initMapInterval);
                    console.log('Map initialized successfully');
                    startUpdates();
                }
            }
            
            attempts++;
            if (attempts > 10) {
                clearInterval(initMapInterval);
                console.error('Failed to initialize map');
                
                // Fallback: Create a new map if Folium map can't be found
                initializeNewMap();
            }
        }, 500);
    }
    
    // Fallback: Initialize a new Leaflet map if the Folium one isn't available
    function initializeNewMap() {
        console.log('Creating new map as fallback');
        // Remove any existing map
        const mapElement = document.getElementById('map');
        mapElement.innerHTML = '';
        
        // Create a new map
        map = L.map('map').setView([20.5937, 78.9629], 5);
        
        // Add a dark-themed tile layer
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(map);
        
        // Add mandi markers
        fetchMandiLocations();
        
        // Start truck updates
        startUpdates();
    }
    
    // Fetch mandi locations (in real app this would come from backend)
    function fetchMandiLocations() {
        fetch('/update-trucks')
            .then(response => response.json())
            .then(data => {
                // Extract unique mandi destinations from truck data
                const mandis = new Set();
                for (const truckId in data) {
                    const truck = data[truckId];
                    if (truck.destination_coords) {
                        mandis.add(JSON.stringify({
                            name: truck.destination,
                            coords: truck.destination_coords
                        }));
                    }
                }
                
                // Add mandi markers
                mandisLayer = L.layerGroup().addTo(map);
                Array.from(mandis).forEach(mandiJson => {
                    const mandi = JSON.parse(mandiJson);
                    L.marker(mandi.coords, {
                        icon: L.divIcon({
                            className: 'mandi-marker',
                            html: `<div class="mandi-icon"><i class="fas fa-store"></i></div>`,
                            iconSize: [30, 30]
                        })
                    })
                    .bindPopup(`<b>${mandi.name} Mandi</b>`)
                    .addTo(mandisLayer);
                });
            })
            .catch(error => console.error('Error fetching mandi data:', error));
    }
    
    // Start periodic updates
    function startUpdates() {
        // Initial update
        updateTruckPositions();
        
        // Set up interval for updates
        updateInterval = setInterval(() => {
            if (updatesActive) {
                updateTruckPositions();
            }
        }, updateFrequency);
    }
    
    // Update truck positions
    function updateTruckPositions() {
        fetch('/update-trucks')
            .then(response => response.json())
            .then(data => {
                updateTruckMarkers(data);
                updateTruckList(data);
                updateLastUpdated();
            })
            .catch(error => console.error('Error updating truck positions:', error));
    }
    
    // Update truck markers on the map
    function updateTruckMarkers(truckData) {
        // First, update or create markers for all trucks
        for (const truckId in truckData) {
            const truck = truckData[truckId];
            const latLng = [truck.lat, truck.lon];
            
            // Determine icon color based on status
            const iconColor = truck.status === 'on-time' ? 'blue' : 'red';
            
            // Create icon options
            const iconOptions = {
                className: `truck-marker status-${truck.status}`,
                html: `<div class="truck-icon"><i class="fas fa-truck"></i></div>`,
                iconSize: [30, 30]
            };
            
            // Create or update marker
            if (truckMarkers[truckId]) {
                // Update existing marker
                truckMarkers[truckId].setLatLng(latLng);
                
                // Update popup content
                const popupContent = `
                    <div class="truck-popup">
                        <h6>${truck.driver}</h6>
                        <div class="truck-details">
                            <p><i class="fas fa-map-marker-alt me-2"></i>Heading to: ${truck.destination}</p>
                            <p><i class="fas fa-clock me-2"></i>ETA: ${truck.eta}</p>
                            <p><i class="fas fa-road me-2"></i>Distance: ${truck.distance.toFixed(1)} km</p>
                        </div>
                    </div>
                `;
                truckMarkers[truckId].getPopup().setContent(popupContent);
            } else {
                // Create new marker
                const marker = L.marker(latLng, {
                    icon: L.divIcon(iconOptions),
                    title: `Truck ${truckId}`
                });
                
                // Add popup
                const popupContent = `
                    <div class="truck-popup">
                        <h6>${truck.driver}</h6>
                        <div class="truck-details">
                            <p><i class="fas fa-map-marker-alt me-2"></i>Heading to: ${truck.destination}</p>
                            <p><i class="fas fa-clock me-2"></i>ETA: ${truck.eta}</p>
                            <p><i class="fas fa-road me-2"></i>Distance: ${truck.distance.toFixed(1)} km</p>
                        </div>
                    </div>
                `;
                marker.bindPopup(popupContent);
                
                // Add to map and store reference
                marker.addTo(map);
                truckMarkers[truckId] = marker;
            }
            
            // Check if truck is within 1km of mandi and play alert
            if (truck.distance < 1) {
                playProximityAlert();
            }
        }
        
        // Remove markers for trucks that no longer exist
        for (const truckId in truckMarkers) {
            if (!truckData[truckId]) {
                map.removeLayer(truckMarkers[truckId]);
                delete truckMarkers[truckId];
            }
        }
    }
    
    // Update truck list in the sidebar
    function updateTruckList(truckData) {
        truckListElement.innerHTML = '';
        
        for (const truckId in truckData) {
            const truck = truckData[truckId];
            
            // Create truck list item
            const truckItem = document.createElement('div');
            truckItem.className = `truck-item status-${truck.status}`;
            
            truckItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <strong>${truck.driver}</strong>
                    <span class="badge ${truck.status === 'on-time' ? 'bg-success' : 'bg-danger'}">
                        ${truck.status === 'on-time' ? 'On Time' : 'Delayed'}
                    </span>
                </div>
                <div class="small text-muted">
                    <div>To: ${truck.destination}</div>
                    <div>ETA: ${truck.eta}</div>
                </div>
            `;
            
            // Add click handler to focus map on this truck
            truckItem.addEventListener('click', () => {
                map.setView([truck.lat, truck.lon], 10);
                truckMarkers[truckId].openPopup();
            });
            
            truckListElement.appendChild(truckItem);
        }
    }
    
    // Update timestamp for last update
    function updateLastUpdated() {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        lastUpdatedElement.textContent = `Updated: ${timeString}`;
    }
    
    // Play proximity alert when truck is within 1km of mandi
    function playProximityAlert() {
        // Check if we should actually play the alert (could add user preference)
        const shouldAlert = true;
        
        if (shouldAlert) {
            // Create a simple beep sound
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.type = 'sine';
            oscillator.frequency.value = 780;
            gainNode.gain.value = 0.3;
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.start();
            setTimeout(() => {
                oscillator.stop();
            }, 300);
        }
    }
    
    // Toggle updates on/off
    toggleUpdatesBtn.addEventListener('click', function() {
        updatesActive = !updatesActive;
        
        if (updatesActive) {
            this.innerHTML = '<i class="fas fa-pause me-1"></i>Pause';
            updateStatusBadge.textContent = 'Updates Active';
            updateStatusBadge.className = 'badge bg-success me-2';
            updateTruckPositions(); // Immediate update
        } else {
            this.innerHTML = '<i class="fas fa-play me-1"></i>Resume';
            updateStatusBadge.textContent = 'Updates Paused';
            updateStatusBadge.className = 'badge bg-warning me-2';
        }
    });
    
    // Initialize the map when the page loads
    initializeMap();
});
