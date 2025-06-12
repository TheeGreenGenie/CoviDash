#COVID-19 DATA FETCHING MODULE

import requests
import time
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetcher:

    def __init__(self, disease_sh_base: str, cdc_base: str, timeout: int = 30):
        self.disease_sh_base = disease_sh_base.rstrip('/')
        self.cdc_base = cdc_base.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()

        self.session.headers.update({
            'User-Agent': 'COVID-Tracker/1.0 (Educational Project)',
            'Accept': 'application/json'
        })

    def fetch_with_retry(self, url: str, max_retries: int = 3, backoff_factor: float = 1.0) -> Optional[Dict]:
        #Returns: JSON data as Dict or None

        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Fetching data from: {url} (attempt {attempt+1})" )
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                if 'application/json' in response.headers.get('content-type', ''):
                    return response.json()
                else:
                    logger.warning(f"Non-JSON response from {url}")
                    return None
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts failde for {url}: {e}")
                    return None
                
        return None
    
    def fetch_global_data(self) -> Optional[Dict]:
        #fetch global data from disease.sh

        url = f"{self.disease_sh_base}/all"
        data = self.fetch_with_retry(url)

        if data and self.validate_global_data(data):
            logger.info("Successfully fetched global COVID-19 data")
            return data
        else:
            logger.error("Failed to fetch or validate global data")
            return None
        
    def fetch_countries_data(self) -> Optional[List[Dict]]:
        url = f"{self.disease_sh_base}/countries"
        data = self.fetch_with_retry(url)

        if data and isinstance(data, list) and len(data) > 0:
            logger.info(f"Successfully fetched data for {len(data)} countries")
            return data
        else:
            logger.error("Failed to fetch countries data")
            return None
        
    def fetch_us_states_data(self) -> Optional[List[Dict]]:
        url = f"{self.disease_sh_base}/states"
        data = self.fetch_with_retry(url)

        if data and isinstance(data, list) and len(data) > 0:
            logger.info(f"Succesfully fetched data for {len(data)} US States")
            return data
        else:
            logger.error("Failed to fetch US states data")
            return None
                
    def fetch_major_cities_data(self) -> List[Dict]:
        
        locations_data = []
    
        countries_data = self.fetch_countries_data()
        if not countries_data:
            logger.error("Cannot fetch locations data without countries data")
            return []
        
        us_states_data = self.fetch_us_states_data()
        state_lookup = {}
        if us_states_data:
            for state in us_states_data:
                state_name = state.get('state', '')
                state_lookup[state_name] = state
        
        major_world_cities = self._get_major_world_cities()
        
        for city in major_world_cities:
            processed_city = self._process_city_data(city, countries_data, state_lookup)
            if processed_city:
                processed_city['type'] = 'city'
                locations_data.append(processed_city)
        
        if us_states_data:
            for state in us_states_data:
                state_location = self._process_state_data(state)
                if state_location:
                    state_location['type'] = 'state'
                    locations_data.append(state_location)
        
        major_countries = self._get_major_countries(countries_data)
        for country in major_countries:
            country_location = self._process_country_data(country)
            if country_location:
                country_location['type'] = 'country'
                locations_data.append(country_location)
        
        logger.info(f"Successfully processed data for {len(locations_data)} locations")
        return locations_data
    
    def fetch_cdc_data(self) -> Optional[Dict]:
        #Returns CDC data dict or None

        #Will update

        logger.info("CDC API Integration not yet implemented")
        return None
    
    def validate_global_data(self, data: Dict) -> bool:
        required_fields = ['cases', 'deaths', 'recovered', 'updated']
        return all(field in data for field in required_fields)
    
    def validate_country_data(self, data: Dict) -> bool:
        required_fields = ['country', 'cases', 'deaths', 'recovered']
        return all(field in data for field in required_fields)
    
    def get_data_summary(self) -> Dict:
        summary = {
            'timestamp': datetime.now().isoformat(),
            'sources': {
                'disease_sh': {
                    'available': False,
                    'global_data': False,
                    'countries_data': False,
                    'us_states_data': False
                },
                'cdc': {
                    'available': False,
                    'implemented': False
                }
            }
        }

        try:
            global_data = self.fetch_global_data()
            summary['sources']['disease_sh']['global_data'] = global_data is not None

            countries_data = self.fetch_countries_data()
            summary['sources']['disease_sh']['countries_data'] = countries_data is not None

            us_states_data = self.fetch_us_states_data()
            summary['sources']['disease_sh']['us_states_data'] = us_states_data is not None

            summary['sources']['disease_sh']['available'] = any([
                summary['sources']['disease_sh']['global_data'],
                summary['sources']['disease_sh']['countries_data'],
                summary['sources']['disease_sh']['us_states_data']
            ])

        except Exception as e:
            logger.error(f"Error testing disease.sh API: {e}")

        return summary
    
    def _get_major_world_cities(self) -> List[Dict]:
        return [
            # North America
            {"name": "New York", "country": "USA", "state": "New York", "lat": 40.7128, "lon": -74.0060, "population": 8336817},
            {"name": "Los Angeles", "country": "USA", "state": "California", "lat": 34.0522, "lon": -118.2437, "population": 3979576},
            {"name": "Chicago", "country": "USA", "state": "Illinois", "lat": 41.8781, "lon": -87.6298, "population": 2693976},
            {"name": "Toronto", "country": "Canada", "lat": 43.6532, "lon": -79.3832, "population": 2731571},
            {"name": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332, "population": 21580000},
            
            # Europe
            {"name": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "population": 9648110},
            {"name": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "population": 2161000},
            {"name": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050, "population": 3669491},
            {"name": "Madrid", "country": "Spain", "lat": 40.4168, "lon": -3.7038, "population": 6642000},
            {"name": "Rome", "country": "Italy", "lat": 41.9028, "lon": 12.4964, "population": 2872800},
            {"name": "Amsterdam", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041, "population": 872680},
            
            # Asia
            {"name": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "population": 37400068},
            {"name": "Beijing", "country": "China", "lat": 39.9042, "lon": 116.4074, "population": 21540000},
            {"name": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "population": 20400000},
            {"name": "Seoul", "country": "South Korea", "lat": 37.5665, "lon": 126.9780, "population": 9720846},
            {"name": "Singapore", "country": "Singapore", "lat": 1.3521, "lon": 103.8198, "population": 5850342},
            {"name": "Bangkok", "country": "Thailand", "lat": 13.7563, "lon": 100.5018, "population": 10350000},
            {"name": "Jakarta", "country": "Indonesia", "lat": -6.2088, "lon": 106.8456, "population": 10560000},
            
            # Middle East & Africa
            {"name": "Dubai", "country": "UAE", "lat": 25.2048, "lon": 55.2708, "population": 3400000},
            {"name": "Istanbul", "country": "Turkey", "lat": 41.0082, "lon": 28.9784, "population": 15460000},
            {"name": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357, "population": 20900000},
            {"name": "Lagos", "country": "Nigeria", "lat": 6.5244, "lon": 3.3792, "population": 15300000},
            {"name": "Johannesburg", "country": "South Africa", "lat": -26.2041, "lon": 28.0473, "population": 4434827},
            
            # South America
            {"name": "São Paulo", "country": "Brazil", "lat": -23.5558, "lon": -46.6396, "population": 12400000},
            {"name": "Buenos Aires", "country": "Argentina", "lat": -34.6118, "lon": -58.3960, "population": 15200000},
            {"name": "Lima", "country": "Peru", "lat": -12.0464, "lon": -77.0428, "population": 10700000},
            
            # Australia
            {"name": "Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "population": 5312163},
            {"name": "Melbourne", "country": "Australia", "lat": -37.8136, "lon": 144.9631, "population": 5078193},
        ]

    def _get_major_countries(self, countries_data: List[Dict]) -> List[Dict]:
        major_countries = []
        
        for country in countries_data:
            population = country.get('population', 0)
            cases = country.get('cases', 0)
            country_name = country.get('country', '')
            
            # Include countries with significant population or cases
            if (population > 10000000 or cases > 100000) and country_name:
                # Add approximate coordinates for major countries (capital cities)
                coordinates = self._get_country_coordinates(country_name)
                if coordinates:
                    country_info = country.copy()
                    country_info.update(coordinates)
                    country_info['display_name'] = country_name
                    major_countries.append(country_info)
        
        # Sort by cases and take top 50 to avoid overcrowding
        major_countries.sort(key=lambda x: x.get('cases', 0), reverse=True)
        return major_countries[:50]

    def _get_country_coordinates(self, country_name: str) -> Dict:
        """Get approximate coordinates for country capitals"""
        country_coords = {
            'USA': {'lat': 38.9072, 'lon': -77.0369},
            'China': {'lat': 39.9042, 'lon': 116.4074},
            'India': {'lat': 28.6139, 'lon': 77.2090},
            'Brazil': {'lat': -15.7942, 'lon': -47.8822},
            'Russia': {'lat': 55.7558, 'lon': 37.6176},
            'UK': {'lat': 51.5074, 'lon': -0.1278},
            'France': {'lat': 48.8566, 'lon': 2.3522},
            'Germany': {'lat': 52.5200, 'lon': 13.4050},
            'Iran': {'lat': 35.6892, 'lon': 51.3890},
            'Turkey': {'lat': 39.9334, 'lon': 32.8597},
            'Italy': {'lat': 41.9028, 'lon': 12.4964},
            'Spain': {'lat': 40.4168, 'lon': -3.7038},
            'Argentina': {'lat': -34.6118, 'lon': -58.3960},
            'Colombia': {'lat': 4.7110, 'lon': -74.0721},
            'Poland': {'lat': 52.2297, 'lon': 21.0122},
            'Ukraine': {'lat': 50.4501, 'lon': 30.5234},
            'South Africa': {'lat': -25.7479, 'lon': 28.2293},
            'Peru': {'lat': -12.0464, 'lon': -77.0428},
            'Indonesia': {'lat': -6.2088, 'lon': 106.8456},
            'Netherlands': {'lat': 52.3676, 'lon': 4.9041},
            'Chile': {'lat': -33.4489, 'lon': -70.6693},
            'Romania': {'lat': 44.4268, 'lon': 26.1025},
            'Israel': {'lat': 31.7683, 'lon': 35.2137},
            'Belgium': {'lat': 50.8503, 'lon': 4.3517},
            'Iraq': {'lat': 33.3152, 'lon': 44.3661},
            'Bangladesh': {'lat': 23.8103, 'lon': 90.4125},
            'Sweden': {'lat': 59.3293, 'lon': 18.0686},
            'Portugal': {'lat': 38.7223, 'lon': -9.1393},
            'Japan': {'lat': 35.6762, 'lon': 139.6503},
            'Serbia': {'lat': 44.7866, 'lon': 20.4489},
            'Switzerland': {'lat': 46.9480, 'lon': 7.4474},
            'Hungary': {'lat': 47.4979, 'lon': 19.0402},
            'Jordan': {'lat': 31.9454, 'lon': 35.9284},
            'Austria': {'lat': 48.2082, 'lon': 16.3738},
            'Morocco': {'lat': 34.0209, 'lon': -6.8416},
            'Lebanon': {'lat': 33.8547, 'lon': 35.8623},
            'Saudi Arabia': {'lat': 24.7136, 'lon': 46.6753},
            'South Korea': {'lat': 37.5665, 'lon': 126.9780},
        }
        
        return country_coords.get(country_name, None)

    def _process_city_data(self, city: Dict, countries_data: List[Dict], state_lookup: Dict) -> Dict:
        try:
            city_data = city.copy()
            
            # Create country lookup
            country_lookup = {}
            for country in countries_data:
                country_name = country.get('country', '')
                country_lookup[country_name] = country
                
                # Handle common name variations
                if country_name == 'United Kingdom':
                    country_lookup['UK'] = country
                elif country_name == 'United States':
                    country_lookup['USA'] = country
                elif country_name == 'Korea, South':
                    country_lookup['South Korea'] = country
            
            # Get country data
            country_data = country_lookup.get(city['country'])
            if not country_data:
                logger.warning(f"No country data found for {city['name']}, {city['country']}")
                return None
            
            # Calculate proportional city data based on population
            country_population = country_data.get('population', 1)
            city_population = city['population']
            population_ratio = city_population / country_population if country_population > 0 else 0.01
            
            # For US cities, try to get state-specific data first
            if city['country'] == 'USA' and 'state' in city:
                state_data = state_lookup.get(city['state'])
                if state_data:
                    # Use state data as base, then calculate city proportion
                    state_population = state_data.get('population', 1)
                    state_city_ratio = city_population / state_population if state_population > 0 else 0.1
                    
                    # Use more realistic city proportions (cities typically have 10-30% of state cases)
                    city_case_ratio = min(state_city_ratio * 1.5, 0.3)  # Cap at 30% of state cases
                    
                    city_data.update({
                        'cases': int(state_data.get('cases', 0) * city_case_ratio),
                        'deaths': int(state_data.get('deaths', 0) * city_case_ratio),
                        'recovered': int(state_data.get('recovered', 0) * city_case_ratio),
                        'active': int(state_data.get('active', 0) * city_case_ratio),
                        'updated': state_data.get('updated'),
                    })
                else:
                    # Fall back to country data with realistic city proportion
                    city_case_ratio = min(population_ratio * 2, 0.15)  # Cap at 15% of country cases
                    
                    city_data.update({
                        'cases': int(country_data.get('cases', 0) * city_case_ratio),
                        'deaths': int(country_data.get('deaths', 0) * city_case_ratio),
                        'recovered': int(country_data.get('recovered', 0) * city_case_ratio),
                        'active': int(country_data.get('active', 0) * city_case_ratio),
                        'updated': country_data.get('updated'),
                    })
            else:
                # For non-US cities, use country data with realistic proportions
                # Major cities typically have higher case rates but cap at reasonable levels
                city_case_ratio = min(population_ratio * 3, 0.2)  # Cap at 20% of country cases
                
                city_data.update({
                    'cases': int(country_data.get('cases', 0) * city_case_ratio),
                    'deaths': int(country_data.get('deaths', 0) * city_case_ratio),
                    'recovered': int(country_data.get('recovered', 0) * city_case_ratio),
                    'active': int(country_data.get('active', 0) * city_case_ratio),
                    'updated': country_data.get('updated'),
                })
            
            # Ensure numbers are realistic
            city_data['cases'] = max(city_data['cases'], 100)  # Minimum case count
            city_data['cases'] = min(city_data['cases'], int(city_population * 0.3))  # Max 30% infection rate

            # Recalculate derived fields with proper relationships
            total_cases = city_data['cases']
            deaths = min(city_data['deaths'], int(total_cases * 0.05))  # Max 5% mortality
            recovered = city_data['recovered']

            # FIXED: Handle missing recovery data - estimate if zero or very low
            recovery_rate = recovered / total_cases if total_cases > 0 else 0
            
            # Initialize estimation flags
            city_data['estimated'] = False
            city_data['estimation'] = None
            
            if recovery_rate < 0.1:  # If less than 10% recovered (unrealistic)
                # Estimate recoveries: assume 85% of non-fatal cases recover over time
                # Leave some active cases for ongoing infections
                estimated_recovered = int((total_cases - deaths) * 0.96)
                
                # Don't exceed realistic limits
                estimated_recovered = min(estimated_recovered, int(total_cases * 0.95))
                
                # Set estimation flags
                city_data['estimated'] = True
                city_data['estimation'] = estimated_recovered
                
                
                # Update recovered to use estimation
                recovered = estimated_recovered
            
            # Ensure deaths + recovered doesn't exceed total cases
            if deaths + recovered > total_cases:
                recovered = max(0, total_cases - deaths)
                # Update estimation if we had to adjust
                if city_data['estimated']:
                    city_data['estimation'] = recovered

            # Calculate active cases
            active_cases = max(0, total_cases - deaths - recovered)

            # If active cases are still unrealistically high (>10% of population), cap them
            max_realistic_active = int(city_population * 0.02)  # Max 2% active infection rate
            if active_cases > max_realistic_active:
                active_cases = max_realistic_active
                # Adjust recovered to make the math work
                recovered = max(0, total_cases - deaths - active_cases)
                # Update estimation if we had to adjust again
                if city_data['estimated']:
                    city_data['estimation'] = recovered

            # Update the data with final realistic numbers
            city_data['deaths'] = deaths
            city_data['recovered'] = recovered
            city_data['active'] = active_cases
            
            
            return city_data
            
        except Exception as e:
            logger.error(f"Error processing city data for {city.get('name', 'Unknown')}: {e}")
            return None

    def _process_state_data(self, state: Dict) -> Dict:
        try:
            state_data = {
                'name': state.get('state', 'Unknown State'),
                'country': 'USA',
                'display_name': f"{state.get('state', 'Unknown State')}, USA",
                'latitude': self._get_state_coordinates(state.get('state', '')).get('lat', 39.8283),
                'longitude': self._get_state_coordinates(state.get('state', '')).get('lon', -98.5795),
                'population': state.get('population', 1000000),  # Default population
                'cases': state.get('cases', 0),
                'deaths': state.get('deaths', 0),
                'recovered': state.get('recovered', 0),
                'active': state.get('active', 0),
                'updated': state.get('updated'),
                'last_updated': datetime.now().isoformat(),
            }
            
            # ADD ESTIMATION LOGIC FOR STATES TOO
            total_cases = state_data['cases']
            deaths = state_data['deaths']
            recovered = state_data['recovered']
            
            # Initialize estimation flags
            state_data['estimated'] = False
            state_data['estimation'] = None
            
            # Check if recovery data is missing or unrealistic (less than 10% recovery rate)
            recovery_rate = recovered / total_cases if total_cases > 0 else 0
            
            if recovery_rate < 0.1 and total_cases > 0:  # If less than 10% recovered (unrealistic)
                # Estimate recoveries: assume 85% of non-fatal cases recover over time
                estimated_recovered = int((total_cases - deaths) * 0.96)
                
                # Don't exceed realistic limits
                estimated_recovered = min(estimated_recovered, int(total_cases * 0.95))
                estimated_recovered = max(estimated_recovered, 0)  # Ensure non-negative
                
                # Set estimation flags
                state_data['estimated'] = True
                state_data['estimation'] = estimated_recovered
                
                
                # Update recovered to use estimation
                state_data['recovered'] = estimated_recovered
                
                # Recalculate active cases
                state_data['active'] = max(0, total_cases - deaths - estimated_recovered)
            
            
            return state_data
            
        except Exception as e:
            logger.error(f"Error processing state data for {state.get('state', 'Unknown')}: {e}")
            return None

    def _process_country_data(self, country: Dict) -> Dict:
        try:
            country_data = {
                'name': country.get('country', 'Unknown Country'),
                'country': country.get('country', 'Unknown Country'),
                'display_name': country.get('country', 'Unknown Country'),
                'latitude': country.get('lat', 0),
                'longitude': country.get('lon', 0),
                'population': country.get('population', 1),
                'cases': country.get('cases', 0),
                'deaths': country.get('deaths', 0),
                'recovered': country.get('recovered', 0),
                'active': country.get('active', 0),
                'updated': country.get('updated'),
                'last_updated': datetime.now().isoformat(),
            }
            
            # ADD ESTIMATION LOGIC FOR COUNTRIES TOO
            total_cases = country_data['cases']
            deaths = country_data['deaths']
            recovered = country_data['recovered']
            
            # Initialize estimation flags
            country_data['estimated'] = False
            country_data['estimation'] = None
            
            # Check if recovery data is missing or unrealistic (less than 10% recovery rate)
            recovery_rate = recovered / total_cases if total_cases > 0 else 0
            
            if recovery_rate < 0.1 and total_cases > 0:  # If less than 10% recovered (unrealistic)
                # Estimate recoveries: assume 85% of non-fatal cases recover over time
                estimated_recovered = int((total_cases - deaths) * 0.96)
                
                # Don't exceed realistic limits
                estimated_recovered = min(estimated_recovered, int(total_cases * 0.95))
                estimated_recovered = max(estimated_recovered, 0)  # Ensure non-negative
                
                # Set estimation flags
                country_data['estimated'] = True
                country_data['estimation'] = estimated_recovered
                
                
                # Update recovered to use estimation
                country_data['recovered'] = estimated_recovered
                
                # Recalculate active cases
                country_data['active'] = max(0, total_cases - deaths - estimated_recovered)
                        
            return country_data
            
        except Exception as e:
            logger.error(f"Error processing country data for {country.get('country', 'Unknown')}: {e}")
            return None

    def _get_state_coordinates(self, state_name: str) -> Dict:
        state_coords = {
            'Alabama': {'lat': 32.3617, 'lon': -86.2792},
            'Alaska': {'lat': 58.3019, 'lon': -134.4197},
            'Arizona': {'lat': 33.4484, 'lon': -112.0740},
            'Arkansas': {'lat': 34.7465, 'lon': -92.2896},
            'California': {'lat': 38.5816, 'lon': -121.4944},
            'Colorado': {'lat': 39.7391, 'lon': -104.9847},
            'Connecticut': {'lat': 41.7658, 'lon': -72.6734},
            'Delaware': {'lat': 39.1612, 'lon': -75.5264},
            'Florida': {'lat': 30.4518, 'lon': -84.27277},
            'Georgia': {'lat': 33.7490, 'lon': -84.3880},
            'Hawaii': {'lat': 21.3099, 'lon': -157.8581},
            'Idaho': {'lat': 43.6150, 'lon': -116.2023},
            'Illinois': {'lat': 39.7817, 'lon': -89.6501},
            'Indiana': {'lat': 39.7910, 'lon': -86.1480},
            'Iowa': {'lat': 41.5888, 'lon': -93.6203},
            'Kansas': {'lat': 39.04, 'lon': -95.69},
            'Kentucky': {'lat': 38.2009, 'lon': -84.8733},
            'Louisiana': {'lat': 30.4515, 'lon': -91.1871},
            'Maine': {'lat': 44.3106, 'lon': -69.7795},
            'Maryland': {'lat': 38.9729, 'lon': -76.5012},
            'Massachusetts': {'lat': 42.2352, 'lon': -71.0275},
            'Michigan': {'lat': 42.3584, 'lon': -84.9551},
            'Minnesota': {'lat': 44.9537, 'lon': -93.0900},
            'Mississippi': {'lat': 32.3540, 'lon': -90.1781},
            'Missouri': {'lat': 38.572954, 'lon': -92.189283},
            'Montana': {'lat': 46.595805, 'lon': -112.027031},
            'Nebraska': {'lat': 40.809868, 'lon': -96.675345},
            'Nevada': {'lat': 39.161921, 'lon': -119.767403},
            'New Hampshire': {'lat': 43.220093, 'lon': -71.549896},
            'New Jersey': {'lat': 40.221741, 'lon': -74.756138},
            'New Mexico': {'lat': 35.667231, 'lon': -105.964575},
            'New York': {'lat': 42.659829, 'lon': -73.781339},
            'North Carolina': {'lat': 35.771, 'lon': -78.638},
            'North Dakota': {'lat': 46.813343, 'lon': -100.779004},
            'Ohio': {'lat': 39.961176, 'lon': -82.998794},
            'Oklahoma': {'lat': 35.482309, 'lon': -97.534994},
            'Oregon': {'lat': 44.931109, 'lon': -123.029159},
            'Pennsylvania': {'lat': 40.269789, 'lon': -76.875613},
            'Rhode Island': {'lat': 41.82355, 'lon': -71.422132},
            'South Carolina': {'lat': 34.000, 'lon': -81.035},
            'South Dakota': {'lat': 44.367966, 'lon': -100.336378},
            'Tennessee': {'lat': 36.165, 'lon': -86.784},
            'Texas': {'lat': 30.266667, 'lon': -97.75},
            'Utah': {'lat': 40.777477, 'lon': -111.888237},
            'Vermont': {'lat': 44.26639, 'lon': -72.58133},
            'Virginia': {'lat': 37.54, 'lon': -77.46},
            'Washington': {'lat': 47.042418, 'lon': -122.893077},
            'West Virginia': {'lat': 38.349497, 'lon': -81.633294},
            'Wisconsin': {'lat': 43.074722, 'lon': -89.384444},
            'Wyoming': {'lat': 41.145548, 'lon': -104.802042},
        }
        
        return state_coords.get(state_name, {'lat': 39.8283, 'lon': -98.5795})  # Default to US center
    
#Conveniency functions    
def create_fetcher(disease_sh_api: str, cdc_api: str) -> DataFetcher:
    return DataFetcher(disease_sh_api, cdc_api)

def fetch_cities_data(disease_sh_api: str, cdc_api: str) -> List[Dict]:
    fetcher = create_fetcher(disease_sh_api, cdc_api)
    return fetcher.fetch_major_cities_data()