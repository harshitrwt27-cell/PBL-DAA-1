from flask import Flask, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
import heapq
import math
import json
from datetime import datetime
import os
from urllib.parse import urlencode

app = Flask(__name__)
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', 'AIzaSyALbCCPqlurlk8Std1nDdBHukPK_FV4Kdw')
BACKEND_BASE_URL = os.environ.get('BACKEND_BASE_URL', 'https://pbl-daa-1-1.onrender.com').rstrip('/')
FRONTEND_BASE_URL = os.environ.get('FRONTEND_BASE_URL', 'https://pbl-daa-frontend.onrender.com').rstrip('/')

# Use DATABASE_URL env var for production-quality DB (MySQL/PostgreSQL), fallback example:
# mysql+pymysql://username:password@localhost:3306/bookings_db
# postgresql+psycopg2://username:password@localhost:5432/bookings_db
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///bookings.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()
db.init_app(app)


@app.after_request
def add_cors_headers(response):
    """Allow frontend clients from other origins to call API endpoints."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@app.route('/api/<path:route>', methods=['OPTIONS'])
def handle_options(route):
    """Handle CORS preflight requests"""
    return '', 204


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    start_stop = db.Column(db.String(255), nullable=True)
    end_stop = db.Column(db.String(255), nullable=True)
    algorithm = db.Column(db.String(50), nullable=True)
    distance = db.Column(db.Float, nullable=True)
    path = db.Column(db.Text, nullable=True)
    map_link = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def init_db():
    with app.app_context():
        db.create_all()

# ============================================================================
# MULTI-REGION BUS NETWORK DATA
# ============================================================================

# Uttarakhand Hilly Region - Major Cities & Routes
UTTARAKHAND_NETWORK = {
    'Dehradun': {
        'coords': (30.1975, 78.1313),
        'region': 'Uttarakhand',
        'stops': {
            'Dehradun Railway Station': (30.2048, 78.1422),
            'Dehradun Bus Stand': (30.1975, 78.1313),
            'Clement Town': (30.1855, 78.0982),
            'Rajpur Road': (30.2145, 78.1245)
        }
    },
    'Rishikesh': {
        'coords': (30.0888, 78.2676),
        'region': 'Uttarakhand',
        'stops': {
            'Rishikesh City': (30.0888, 78.2676),
            'Neelkanth Area': (30.1250, 78.2450)
        }
    },
    'Mussoorie': {
        'coords': (30.4627, 78.4660),
        'region': 'Uttarakhand',
        'stops': {
            'Mussoorie Main': (30.4627, 78.4660),
            'Mall Road': (30.4700, 78.4750)
        }
    },
    'Nainital': {
        'coords': (29.3919, 79.4504),
        'region': 'Uttarakhand',
        'stops': {
            'Nainital City': (29.3919, 79.4504),
            'Nainital Bus Station': (29.3900, 79.4450)
        }
    },
    'Almora': {
        'coords': (29.5882, 79.6450),
        'region': 'Uttarakhand',
        'stops': {
            'Almora City': (29.5882, 79.6450)
        }
    },
    'Haldwani': {
        'coords': (29.2167, 79.5167),
        'region': 'Uttarakhand',
        'stops': {
            'Haldwani City': (29.2167, 79.5167)
        }
    },
    'Kashipur': {
        'coords': (29.2084, 79.3833),
        'region': 'Uttarakhand',
        'stops': {
            'Kashipur City': (29.2084, 79.3833)
        }
    },
    'Rudraprayag': {
        'coords': (30.2802, 78.9856),
        'region': 'Uttarakhand',
        'stops': {
            'Rudraprayag': (30.2802, 78.9856)
        }
    },
    'Chopta': {
        'coords': (30.3969, 79.2428),
        'region': 'Uttarakhand',
        'stops': {
            'Chopta': (30.3969, 79.2428)
        }
    }
}

# India Wide Highway Network
INDIA_HIGHWAYS = {
    'Delhi': {
        'coords': (28.6139, 77.2090),
        'region': 'North',
        'stops': {
            'Delhi ISBT Kashmere': (28.6505, 77.2272),
            'Delhi Airport': (28.5562, 77.1000)
        }
    },
    'Jaipur': {
        'coords': (26.9124, 75.7873),
        'region': 'North',
        'stops': {
            'Jaipur City': (26.9124, 75.7873)
        }
    },
    'Agra': {
        'coords': (27.1767, 78.0081),
        'region': 'North',
        'stops': {
            'Agra City': (27.1767, 78.0081)
        }
    },
    'Mumbai': {
        'coords': (19.0760, 72.8777),
        'region': 'West',
        'stops': {
            'Mumbai Central': (19.0760, 72.8777)
        }
    },
    'Bangalore': {
        'coords': (12.9716, 77.5946),
        'region': 'South',
        'stops': {
            'Bangalore City': (12.9716, 77.5946)
        }
    },
    'Chennai': {
        'coords': (13.0827, 80.2707),
        'region': 'South',
        'stops': {
            'Chennai Central': (13.0827, 80.2707)
        }
    },
    'Kolkata': {
        'coords': (22.5726, 88.3639),
        'region': 'East',
        'stops': {
            'Kolkata City': (22.5726, 88.3639)
        }
    },
    'Hyderabad': {
        'coords': (17.3850, 78.4867),
        'region': 'South',
        'stops': {
            'Hyderabad City': (17.3850, 78.4867)
        }
    },
    'Pune': {
        'coords': (18.5204, 73.8567),
        'region': 'West',
        'stops': {
            'Pune City': (18.5204, 73.8567)
        }
    },
    'Chandigarh': {
        'coords': (30.7333, 76.7794),
        'region': 'North',
        'stops': {
            'Chandigarh City': (30.7333, 76.7794)
        }
    }
}

# Region Definitions
REGIONS = {
    'Uttarakhand': {
        'name': 'Uttarakhand Hilly Region',
        'network': UTTARAKHAND_NETWORK,
        'bounds': [[29.0, 78.0], [31.0, 81.0]]
    },
    'India': {
        'name': 'India Wide Highways',
        'network': INDIA_HIGHWAYS,
        'bounds': [[8.0, 68.0], [35.0, 97.0]]
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def haversine(coord1, coord2):
    """Calculate distance between two coordinates in km"""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  # Earth's radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return round(R * c, 2)

def build_region_graph(region_key):
    """Build distance graph for a specific region"""
    region_data = REGIONS[region_key]
    network = region_data['network']
    graph = {}
    coordinates = {}
    
    # Build stops and coordinates
    for city, city_data in network.items():
        for stop_name, stop_coords in city_data['stops'].items():
            full_stop_name = f"{city}: {stop_name}"
            coordinates[full_stop_name] = stop_coords
            graph[full_stop_name] = []
    
    # Add within-city connections
    for city, city_data in network.items():
        city_stops = [f"{city}: {stop_name}" for stop_name in city_data['stops'].keys()]
        for i, stop1 in enumerate(city_stops):
            for stop2 in city_stops[i+1:]:
                dist = haversine(coordinates[stop1], coordinates[stop2])
                graph[stop1].append((stop2, dist))
                graph[stop2].append((stop1, dist))
    
    # Connect all stops in a city to the hub stop (first stop)
    for city, city_data in network.items():
        hub_stop = f"{city}: {list(network[city]['stops'].keys())[0]}"
        city_stops = [f"{city}: {stop_name}" for stop_name in city_data['stops'].keys()]
        for stop in city_stops:
            if stop != hub_stop:
                dist = haversine(coordinates[stop], coordinates[hub_stop])
                if (hub_stop, dist) not in graph[stop]:
                    graph[stop].append((hub_stop, dist))
                if (stop, dist) not in graph[hub_stop]:
                    graph[hub_stop].append((stop, dist))
    
    # Add inter-city connections
    cities_list = list(network.keys())
    for i, city1 in enumerate(cities_list):
        stop1 = f"{city1}: {list(network[city1]['stops'].keys())[0]}"
        
        distances_to_cities = []
        for city2 in cities_list:
            if city1 != city2:
                stop2 = f"{city2}: {list(network[city2]['stops'].keys())[0]}"
                dist = haversine(coordinates[stop1], coordinates[stop2])
                distances_to_cities.append((dist, city2, stop2))
        
        # Connect to 3-4 nearest cities
        for dist, city2, stop2 in sorted(distances_to_cities)[:4]:
            if (stop2, dist) not in graph[stop1]:
                graph[stop1].append((stop2, dist))
            if (stop1, dist) not in graph[stop2]:
                graph[stop2].append((stop1, dist))
    
    return graph, coordinates

def find_nearest_stop(user_lat, user_lon, coordinates):
    """Find the nearest bus stop to user's location"""
    if not coordinates:
        return None, float("inf")
    
    nearest_stop = None
    min_distance = float("inf")
    
    for stop, coords in coordinates.items():
        distance = haversine((user_lat, user_lon), coords)
        if distance < min_distance:
            min_distance = distance
            nearest_stop = stop
    
    return nearest_stop, min_distance

# ============================================================================
# ALGORITHMS
# ============================================================================

def dijkstra(graph, start, end):
    """Dijkstra's shortest path algorithm"""
    if start not in graph or end not in graph:
        return float("inf"), []
    
    pq = [(0, start, [])]
    visited = set()

    while pq:
        (cost, node, path) = heapq.heappop(pq)

        if node in visited:
            continue

        path = path + [node]
        visited.add(node)

        if node == end:
            return cost, path

        for neighbor, weight in graph[node]:
            if neighbor not in visited:
                heapq.heappush(pq, (cost + weight, neighbor, path))

    return float("inf"), []

def heuristic(node, end, coordinates):
    """Heuristic function for A*"""
    if node not in coordinates or end not in coordinates:
        return 0
    
    lat1, lon1 = coordinates[node]
    lat2, lon2 = coordinates[end]
    return haversine((lat1, lon1), (lat2, lon2)) * 0.8

def a_star(graph, start, end, coordinates):
    """A* algorithm with heuristic"""
    if start not in graph or end not in graph:
        return float("inf"), []
    
    pq = [(heuristic(start, end, coordinates), 0, start, [])]
    visited = set()
    g_score = {node: float("inf") for node in graph}
    g_score[start] = 0

    while pq:
        (f_score, g_cost, node, path) = heapq.heappop(pq)

        if node in visited:
            continue

        path = path + [node]
        visited.add(node)

        if node == end:
            return g_cost, path

        for neighbor, weight in graph[node]:
            if neighbor not in visited:
                tentative_g = g_cost + weight
                if tentative_g < g_score.get(neighbor, float("inf")):
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, end, coordinates)
                    heapq.heappush(pq, (f_score, tentative_g, neighbor, path))

    return float("inf"), []

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def home():
    return redirect(f"{FRONTEND_BASE_URL}/index")

@app.route('/route/<region>')
def route_finder(region):
    if region not in REGIONS:
        region = 'Uttarakhand'

    return redirect(f"{FRONTEND_BASE_URL}/route?{urlencode({'region': region})}")

@app.route('/api/find-route', methods=['POST'])
def api_find_route():
    """API endpoint for finding routes"""
    data = request.json
    region = data.get('region', 'Uttarakhand')
    start = data.get('start')
    end = data.get('end')
    algorithm = data.get('algorithm', 'dijkstra')
    
    if region not in REGIONS:
        return jsonify({'error': 'Invalid region'}), 400
    
    graph, coordinates = build_region_graph(region)
    
    if start not in graph or end not in graph:
        return jsonify({'error': 'Invalid bus stop'}), 400
    
    if start == end:
        return jsonify({
            'distance': 0,
            'path': [start],
            'stops': 1,
            'time': 0,
            'algorithm': algorithm
        })
    
    if algorithm == 'dijkstra':
        distance, path = dijkstra(graph, start, end)
    elif algorithm == 'a_star':
        distance, path = a_star(graph, start, end, coordinates)
    else:
        return jsonify({'error': 'Invalid algorithm'}), 400
    
    if distance == float("inf"):
        return jsonify({'error': 'No route found'}), 404
    
    # Calculate other algorithm result for comparison
    if algorithm == 'dijkstra':
        alt_dist, _ = a_star(graph, start, end, coordinates)
    else:
        alt_dist, _ = dijkstra(graph, start, end)
    
    comparison = None
    if alt_dist != float("inf"):
        comparison = f"{'A*' if algorithm == 'dijkstra' else 'Dijkstra'} found same route: {alt_dist} km"

    map_link = None
    if path and len(path) >= 2:
        origin = coordinates[path[0]]
        destination = coordinates[path[-1]]
        waypoints = path[1:-1]
        waypoints_str = '|'.join([f"{coordinates[stop][0]},{coordinates[stop][1]}" for stop in waypoints]) if waypoints else ''
        map_link = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={origin[0]},{origin[1]}"
            f"&destination={destination[0]},{destination[1]}"
            f"{f'&waypoints={waypoints_str}' if waypoints_str else ''}"
            f"&travelmode=transit"
        )

    return jsonify({
        'distance': distance,
        'path': path,
        'stops': len(path),
        'time': round(distance / 40, 1),  # Assuming 40 km/h average
        'algorithm': algorithm,
        'comparison': comparison,
        'map_link': map_link,
        'coordinates': [[coordinates[stop][0], coordinates[stop][1]] for stop in path]
    })

@app.route('/api/get-nearest-stop', methods=['POST'])
def api_get_nearest_stop():
    """API endpoint to find nearest stop to user's location"""
    data = request.json
    user_lat = data.get('lat')
    user_lon = data.get('lon')
    region = data.get('region', 'Uttarakhand')
    
    if not user_lat or not user_lon:
        return jsonify({'error': 'Location not provided'}), 400
    
    graph, coordinates = build_region_graph(region)
    
    nearest_stop, distance = find_nearest_stop(user_lat, user_lon, coordinates)
    
    if nearest_stop:
        return jsonify({
            'nearest_stop': nearest_stop,
            'distance': round(distance, 2),
            'coordinates': coordinates[nearest_stop]
        })
    else:
        return jsonify({'error': 'No stops found'}), 404

@app.route('/api/book-route', methods=['POST'])
def api_book_route():
    data = request.json
    name = data.get('name', 'Anonymous')
    region = data.get('region', 'Uttarakhand')
    start = data.get('start')
    end = data.get('end')
    algorithm = data.get('algorithm', 'dijkstra')
    distance = data.get('distance')
    path = data.get('path')
    map_link = data.get('map_link')

    if not start or not end or not path or distance is None:
        return jsonify({'error': 'Missing booking data'}), 400

    if region not in REGIONS:
        return jsonify({'error': 'Invalid region'}), 400

    if not map_link:
        coordinates = build_region_graph(region)[1]
        if path and len(path) >= 2:
            origin = coordinates[path[0]]
            destination = coordinates[path[-1]]
            waypoints = path[1:-1]
            waypoints_str = '|'.join([f"{coordinates[stop][0]},{coordinates[stop][1]}" for stop in waypoints]) if waypoints else ''
            map_link = (
                f"https://www.google.com/maps/dir/?api=1"
                f"&origin={origin[0]},{origin[1]}"
                f"&destination={destination[0]},{destination[1]}"
                f"{f'&waypoints={waypoints_str}' if waypoints_str else ''}"
                f"&travelmode=transit"
            )

    booking = Booking(
        name=name,
        region=region,
        start_stop=start,
        end_stop=end,
        algorithm=algorithm,
        distance=distance,
        path=json.dumps(path, ensure_ascii=False),
        map_link=map_link,
        created_at=datetime.utcnow()
    )

    db.session.add(booking)
    db.session.commit()
    booking_id = booking.id

    return jsonify({
        'status': 'success',
        'booking_id': booking_id,
        'map_link': map_link,
        'message': 'Booking saved. Open the Google Maps link for route directions.'
    })

@app.route('/network/<region>')
def network(region):
    if region not in REGIONS:
        region = 'Uttarakhand'

    start = request.args.get('start')
    end = request.args.get('end')
    algorithm = request.args.get('algorithm')

    query_params = {'region': region}
    if start:
        query_params['start'] = start
    if end:
        query_params['end'] = end
    if algorithm:
        query_params['algorithm'] = algorithm

    return redirect(f"{FRONTEND_BASE_URL}/network?{urlencode(query_params)}")

@app.route('/api/get-stops', methods=['POST'])
def api_get_stops():
    """API endpoint to get all stops for a region"""
    data = request.json
    region = data.get('region', 'Uttarakhand')
    
    if region not in REGIONS:
        return jsonify({'error': 'Invalid region'}), 400
    
    graph, _ = build_region_graph(region)
    stops = sorted(list(graph.keys()))
    
    return jsonify({'stops': stops})

@app.route('/api/get-network', methods=['POST'])
def api_get_network():
    """API endpoint to get network data (coordinates and graph) for a region"""
    data = request.json
    region = data.get('region', 'Uttarakhand')
    
    if region not in REGIONS:
        return jsonify({'error': 'Invalid region'}), 400
    
    graph, coordinates = build_region_graph(region)
    
    # Convert coordinates dict to JSON-serializable format
    coordinates_serialized = {stop: list(coords) for stop, coords in coordinates.items()}
    
    # Convert graph dict (with tuples) to JSON-serializable format
    graph_serialized = {stop: [[neighbor, dist] for neighbor, dist in connections] 
                       for stop, connections in graph.items()}
    
    return jsonify({
        'coordinates': coordinates_serialized,
        'graph': graph_serialized
    })

@app.route('/api/health', methods=['GET'])
def api_health():
    """Simple health endpoint for frontend connectivity checks."""
    return jsonify({
        'status': 'ok',
        'service': 'bus-route-optimizer-api'
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
