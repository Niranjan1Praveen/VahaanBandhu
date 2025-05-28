document.addEventListener('DOMContentLoaded', function() {
    // Variables to store map elements
    let map;
    let truckMarker;
    let userMarker;
    let mandiMarker;
    let routeLayer1;      // Route from truck to user
    let routeLayer2;      // Route from user to mandi
    let animatedTruckMarker; // For the animated moving truck
    let animationTimer;   // Timer for truck animation
    
    // Get DOM elements
    const mandiSelect = document.getElementById('mandi-select');
    const getRouteBtn = document.getElementById('get-route-btn');
    const routeInfo = document.getElementById('route-info');
    const routeInstructions = document.getElementById('route-instructions');
    const mandiNameElement = document.getElementById('mandi-name');
    const routeDistanceElement = document.getElementById('route-distance');
    const routeDurationElement = document.getElementById('route-duration');
    const alertProximityElement = document.getElementById('alert-proximity');
    const etaValueElement = document.getElementById('eta-value');
    const progressBarElement = document.getElementById('progress-bar');
    
    // Get positions from hidden inputs for initial values
    const truckOriginLat = parseFloat(document.getElementById('truck-origin-lat').value);
    const truckOriginLng = parseFloat(document.getElementById('truck-origin-lng').value);
    let userLat = parseFloat(document.getElementById('user-lat').value);
    let userLng = parseFloat(document.getElementById('user-lng').value);
    
    // Get user location input elements
    const userLocationLatInput = document.getElementById('user-location-lat');
    const userLocationLngInput = document.getElementById('user-location-lng');
    const useMyLocationBtn = document.getElementById('use-my-location');
    
    // Update the user location input fields with initial values
    userLocationLatInput.value = userLat;
    userLocationLngInput.value = userLng;
    
    // Initialize map from the Folium-generated one
    function initializeMap() {
        // Skip trying to find Folium map and create our own directly
        // This avoids the map initialization errors
        console.log('Creating new map directly');
        initializeNewMap();
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
        
        // Initialize markers
        initializeMarkers();
    }
    
    // Initialize all markers on the map
    function initializeMarkers() {
        // Create custom icon for truck origin
        const truckIcon = L.divIcon({
            className: 'origin-marker',
            html: '<i class="fas fa-truck"></i>',
            iconSize: [30, 30]
        });
        
        // Create custom icon for user
        const userIcon = L.divIcon({
            className: 'user-marker',
            html: '<i class="fas fa-user"></i>',
            iconSize: [30, 30]
        });
        
        // Add truck origin marker to map
        truckMarker = L.marker([truckOriginLat, truckOriginLng], {
            icon: truckIcon,
            title: 'Truck Origin'
        }).addTo(map);
        
        // Add popup to truck marker
        truckMarker.bindPopup('<b>Truck Origin</b>');
        
        // Add user marker to map
        userMarker = L.marker([userLat, userLng], {
            icon: userIcon,
            title: 'Your Location'
        }).addTo(map);
        
        // Add popup to user marker
        userMarker.bindPopup('<b>Your Location</b>');
        
        // Create bounds to show both markers
        const bounds = L.latLngBounds([
            [truckOriginLat, truckOriginLng],
            [userLat, userLng]
        ]);
        
        // Fit map to bounds
        map.fitBounds(bounds, { padding: [50, 50] });
    }
    
    // Get the route to the selected mandi
    getRouteBtn.addEventListener('click', function() {
        const selectedMandi = mandiSelect.value;
        
        if (!selectedMandi) {
            alert('Please select a mandi first');
            return;
        }
        
        // Show loading indicator
        this.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Loading...';
        this.disabled = true;
        
        // Prepare data for the request
        const routeData = {
            mandi: selectedMandi,
            truckLat: truckOriginLat,
            truckLng: truckOriginLng,
            userLat: userLat,
            userLng: userLng
        };
        
        // Send request to get route
        fetch('/get-route', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(routeData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to get route');
            }
            return response.json();
        })
        .then(data => {
            displayRoute(data);
        })
        .catch(error => {
            console.error('Error getting route:', error);
            alert('Failed to get route. Please try again.');
        })
        .finally(() => {
            // Reset button
            this.innerHTML = '<i class="fas fa-directions me-1"></i>Get Route';
            this.disabled = false;
        });
    });
    
    // Display the animated route on the map
    function displayRoute(routeData) {
        // Clear any existing routes and animated markers
        clearExistingRoutes();
        
        // Add mandi marker
        const mandiIcon = L.divIcon({
            className: 'mandi-marker',
            html: '<i class="fas fa-store"></i>',
            iconSize: [30, 30]
        });
        
        mandiMarker = L.marker(routeData.mandiLocation, {
            icon: mandiIcon,
            title: routeData.mandi
        }).addTo(map);
        
        mandiMarker.bindPopup(`<b>${routeData.mandi} Mandi</b>`);
        
        // Split the route coordinates into two segments if needed
        const coordinates = routeData.coordinates;
        if (!coordinates || coordinates.length === 0) {
            console.error('No route coordinates found');
            return;
        }
        
        // Find the index that is closest to user location
        let userSegmentIndex = findClosestPointIndex(coordinates, [userLat, userLng]);
        
        // Split the route into two segments
        const segment1 = coordinates.slice(0, userSegmentIndex + 1);
        const segment2 = coordinates.slice(userSegmentIndex);
        
        // Draw first route segment (truck to user)
        routeLayer1 = L.polyline(segment1, {
            color: '#0d6efd',
            weight: 5,
            opacity: 0.8,
            dashArray: '10, 10',
            lineCap: 'round'
        }).addTo(map);
        
        // Draw second route segment (user to mandi)
        routeLayer2 = L.polyline(segment2, {
            color: '#28a745',
            weight: 5,
            opacity: 0.8,
            lineCap: 'round'
        }).addTo(map);
        
        // Fit the map to show the entire route
        const allPoints = [
            routeData.truckOrigin,
            routeData.userLocation,
            routeData.mandiLocation
        ];
        const bounds = L.latLngBounds(allPoints);
        map.fitBounds(bounds, { padding: [50, 50] });
        
        // Start truck animation
        startTruckAnimation(segment1, segment2);
        
        // Update route info panel
        updateRouteInfo(routeData);
    }
    
    // Find the index of the point in coordinates that is closest to target
    function findClosestPointIndex(coordinates, target) {
        let closestIndex = 0;
        let closestDistance = Number.MAX_VALUE;
        
        coordinates.forEach((coord, index) => {
            const distance = calculateDistance(coord[0], coord[1], target[0], target[1]);
            if (distance < closestDistance) {
                closestDistance = distance;
                closestIndex = index;
            }
        });
        
        return closestIndex;
    }
    
    // Calculate distance between two points (using Haversine formula)
    function calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Radius of the earth in km
        const dLat = deg2rad(lat2 - lat1);
        const dLon = deg2rad(lon2 - lon1);
        const a = 
            Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) * 
            Math.sin(dLon/2) * Math.sin(dLon/2); 
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
        const d = R * c; // Distance in km
        return d;
    }
    
    function deg2rad(deg) {
        return deg * (Math.PI/180);
    }
    
    // Animate the truck moving along the route
    function startTruckAnimation(segment1, segment2) {
        // Clear any existing animation
        if (animationTimer) {
            clearInterval(animationTimer);
        }
        
        if (animatedTruckMarker) {
            map.removeLayer(animatedTruckMarker);
        }
        
        // Create a moving truck icon
        const truckIcon = L.divIcon({
            className: 'animated-truck',
            html: '<div class="truck-icon active-truck"><i class="fas fa-truck"></i></div>',
            iconSize: [40, 40]
        });
        
        // Add initial truck marker at the first point of the route
        if (segment1.length > 0) {
            animatedTruckMarker = L.marker(segment1[0], {
                icon: truckIcon,
                title: 'Truck'
            }).addTo(map);
        }
        
        // Variables for animation
        const combinedSegments = [...segment1, ...segment2.slice(1)];
        let currentIndex = 0;
        const totalPoints = combinedSegments.length;
        const animationSpeed = 500; // milliseconds between movements
        
        // Start animation loop
        animationTimer = setInterval(() => {
            currentIndex++;
            
            // Update progress bar
            const progress = (currentIndex / (totalPoints - 1)) * 100;
            progressBarElement.style.width = `${progress}%`;
            
            // Check if animation is complete
            if (currentIndex >= totalPoints) {
                clearInterval(animationTimer);
                return;
            }
            
            // Move truck to next point
            const nextPoint = combinedSegments[currentIndex];
            animatedTruckMarker.setLatLng(nextPoint);
            
            // If truck has reached user location (end of segment1)
            if (currentIndex === segment1.length - 1) {
                // Flash the user marker briefly
                userMarker.setIcon(L.divIcon({
                    className: 'user-marker active-truck',
                    html: '<i class="fas fa-user"></i>',
                    iconSize: [30, 30]
                }));
                
                setTimeout(() => {
                    userMarker.setIcon(L.divIcon({
                        className: 'user-marker',
                        html: '<i class="fas fa-user"></i>',
                        iconSize: [30, 30]
                    }));
                }, 2000);
            }
            
            // If truck is close to destination, trigger alert
            if (currentIndex > totalPoints - 5) {
                alertProximityElement.classList.remove('d-none');
                playProximityAlert();
            }
        }, animationSpeed);
    }
    
    // Update the route information panel
    function updateRouteInfo(routeData) {
        // Show route info panel
        routeInfo.classList.add('active');
        routeInstructions.style.display = 'none';
        
        // Update info
        mandiNameElement.textContent = routeData.mandi;
        
        // Format distance
        const distance = routeData.distance;
        routeDistanceElement.textContent = `${distance.toFixed(1)} km`;
        
        // Format duration and ETA
        const duration = routeData.duration;
        let durationText = '';
        if (duration >= 60) {
            const hours = Math.floor(duration / 60);
            const minutes = Math.round(duration % 60);
            durationText = `${hours} hr ${minutes} min`;
        } else {
            durationText = `${Math.round(duration)} min`;
        }
        routeDurationElement.textContent = durationText;
        
        // Update ETA value
        etaValueElement.textContent = Math.round(duration);
        
        // Show proximity alert if distance is less than 1km
        if (distance < 1) {
            alertProximityElement.classList.remove('d-none');
            playProximityAlert();
        } else {
            alertProximityElement.classList.add('d-none');
        }
    }
    
    // Clear any existing routes and animated elements
    function clearExistingRoutes() {
        if (routeLayer1) {
            map.removeLayer(routeLayer1);
        }
        
        if (routeLayer2) {
            map.removeLayer(routeLayer2);
        }
        
        if (mandiMarker) {
            map.removeLayer(mandiMarker);
        }
        
        if (animatedTruckMarker) {
            map.removeLayer(animatedTruckMarker);
        }
        
        if (animationTimer) {
            clearInterval(animationTimer);
        }
        
        // Reset progress bar
        progressBarElement.style.width = '0%';
        
        // Hide proximity alert
        alertProximityElement.classList.add('d-none');
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
    
    // Add event listener for the "Use My Location" button
    useMyLocationBtn.addEventListener('click', function() {
        if (navigator.geolocation) {
            // Show loading indicator
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
            this.disabled = true;
            
            // Try to get user's current position
            navigator.geolocation.getCurrentPosition(
                // Success callback
                function(position) {
                    // Update the input fields
                    userLocationLatInput.value = position.coords.latitude.toFixed(6);
                    userLocationLngInput.value = position.coords.longitude.toFixed(6);
                    
                    // Update the variables
                    userLat = position.coords.latitude;
                    userLng = position.coords.longitude;
                    
                    // Update the user marker on the map
                    if (userMarker) {
                        userMarker.setLatLng([userLat, userLng]);
                    }
                    
                    // Fit map to show both markers
                    const bounds = L.latLngBounds([
                        [truckOriginLat, truckOriginLng],
                        [userLat, userLng]
                    ]);
                    map.fitBounds(bounds, { padding: [50, 50] });
                    
                    // Reset button
                    useMyLocationBtn.innerHTML = '<i class="fas fa-crosshairs me-1"></i>Use My Location';
                    useMyLocationBtn.disabled = false;
                    
                    // Show success message
                    alert('Your location has been updated successfully!');
                },
                // Error callback
                function(error) {
                    console.error('Error getting location:', error);
                    
                    let errorMessage = 'Unable to retrieve your location. ';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            errorMessage += 'Please allow location access in your browser settings.';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMessage += 'Location information is unavailable.';
                            break;
                        case error.TIMEOUT:
                            errorMessage += 'The request to get your location timed out.';
                            break;
                        case error.UNKNOWN_ERROR:
                            errorMessage += 'An unknown error occurred.';
                            break;
                    }
                    
                    alert(errorMessage);
                    
                    // Reset button
                    useMyLocationBtn.innerHTML = '<i class="fas fa-crosshairs me-1"></i>Use My Location';
                    useMyLocationBtn.disabled = false;
                },
                // Options
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        } else {
            alert('Geolocation is not supported by this browser.');
        }
    });
    
    // Add event listeners to update user location when input fields change
    userLocationLatInput.addEventListener('change', updateUserMarker);
    userLocationLngInput.addEventListener('change', updateUserMarker);
    
    function updateUserMarker() {
        // Get values from inputs
        const newLat = parseFloat(userLocationLatInput.value);
        const newLng = parseFloat(userLocationLngInput.value);
        
        // Validate input
        if (isNaN(newLat) || isNaN(newLng) || newLat < -90 || newLat > 90 || newLng < -180 || newLng > 180) {
            alert('Please enter valid coordinates. Latitude must be between -90 and 90, and longitude between -180 and 180.');
            return;
        }
        
        // Update variables
        userLat = newLat;
        userLng = newLng;
        
        // Update marker on map
        if (userMarker) {
            userMarker.setLatLng([userLat, userLng]);
            
            // Fit map to show both markers
            const bounds = L.latLngBounds([
                [truckOriginLat, truckOriginLng],
                [userLat, userLng]
            ]);
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }
    
    // Modified version of the get route button click handler
    getRouteBtn.addEventListener('click', function() {
        const selectedMandi = mandiSelect.value;
        
        if (!selectedMandi) {
            alert('Please select a mandi first');
            return;
        }
        
        // Get the latest user location values from the input fields
        const latValue = parseFloat(userLocationLatInput.value);
        const lngValue = parseFloat(userLocationLngInput.value);
        
        // Validate input
        if (isNaN(latValue) || isNaN(lngValue) || latValue < -90 || latValue > 90 || lngValue < -180 || lngValue > 180) {
            alert('Please enter valid coordinates. Latitude must be between -90 and 90, and longitude between -180 and 180.');
            return;
        }
        
        // Update the user location variables
        userLat = latValue;
        userLng = lngValue;
        
        // Show loading indicator
        this.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Loading...';
        this.disabled = true;
        
        // Prepare data for the request with the updated user location
        const routeData = {
            mandi: selectedMandi,
            truckLat: truckOriginLat,
            truckLng: truckOriginLng,
            userLat: userLat,
            userLng: userLng
        };
        
        // Send request to get route
        fetch('/get-route', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(routeData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to get route');
            }
            return response.json();
        })
        .then(data => {
            displayRoute(data);
        })
        .catch(error => {
            console.error('Error getting route:', error);
            alert('Failed to get route. Please try again.');
        })
        .finally(() => {
            // Reset button
            this.innerHTML = '<i class="fas fa-directions me-1"></i>Calculate Route';
            this.disabled = false;
        });
    });
    
    // Initialize the map when the page loads
    initializeMap();
});
