#Data processing

import logging
from typing import Dict, List, Optional, Union
from datetime import datetime
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:

    def __init__(self):
        self.processed_data = []
        self.last_processed = None

    def calculate_infection_rate(self, cases: int, population: int) -> float:
        #Returns: Infection rate per 100 people

        if population <= 0:
            return 0.0
        
        rate = (cases / population) * 100000
        return round(rate, 2)
    
    def calculate_mortality_rate(self, deaths: int, cases: int) -> float:
        #Returns mortality rate as %

        if cases <= 0:
            return 0.0
        
        rate = (deaths / cases) * 100
        return round(rate, 2)
    
    def calculate_recovery_rate(self, recovered: int, cases: int) -> float:
        #Returns recovery rate as %

        if cases <= 0:
            return 0.0
        
        rate = (recovered / cases) * 100
        return round(rate, 2)
    
    def get_risk_level(self, infection_rate: float) -> str:
        #Return str analyzing risk for infection [critical, high, medium, low]
        
        if infection_rate >= 5000:
            return 'critical'
        elif infection_rate >= 2000:
            return 'high'
        elif infection_rate >= 500:
            return 'medium'
        else:
            return 'low'
        
    def get_marker_color(self, infection_rate: float) -> str:
        #Returns color

        if infection_rate >= 5000:
            return '#800026'
        elif infection_rate >= 2000:
            return '#BD0026'  
        elif infection_rate >= 1000:
            return '#E31A1C'  
        elif infection_rate >= 500:
            return '#FC4E2A'  
        elif infection_rate >= 100:
            return '#FD8D3C'  
        else:
            return '#FEB24C'  
        
    def format_number(self, number: Union[int, float]) -> str:
        #Returns formatted str

        if number is None:
            return '0'
        
        if number >= 1_000_000_000:
            return f"{number / 1_000_000_000:.1f}B"
        elif number >= 1_000_000:
            return f"{number / 1_000_000:.1f}M"
        elif number >= 1_000:
            return f"{number / 1_000:.1f}K"
        else:
            return str(int(number))
        
    def clean_city_data(self, location_data: Dict) -> Dict:
        #Returns cleaned city data dict

        cleaned = {}
        
        # Required fields with defaults
        cleaned['name'] = location_data.get('name', 'Unknown Location')
        cleaned['country'] = location_data.get('country', 'Unknown Country')
        cleaned['latitude'] = float(location_data.get('latitude', location_data.get('lat', 0)))
        cleaned['longitude'] = float(location_data.get('longitude', location_data.get('lon', 0)))
        cleaned['population'] = int(location_data.get('population', 1))  # Avoid division by zero
        
        # Add location type and display name
        cleaned['type'] = location_data.get('type', 'city')
        cleaned['display_name'] = location_data.get('display_name', f"{cleaned['name']}, {cleaned['country']}")
        
        # COVID data with defaults
        cleaned['cases'] = int(location_data.get('cases', 0))
        cleaned['deaths'] = int(location_data.get('deaths', 0))
        cleaned['recovered'] = int(location_data.get('recovered', 0))

        cleaned['estimated'] = location_data.get('estimated', False)
        cleaned['estimation'] = location_data.get('estimation', None)

        total_cases = cleaned['cases']
        deaths = cleaned['deaths'] 
        recovered = cleaned['recovered']
        raw_active = max(0, total_cases - deaths - recovered)

        recovery_rate = (recovered / total_cases) if total_cases > 0 else 0

        if recovery_rate < 0.1:
            conservative_active = min(raw_active, int(cleaned['population'] * 0.02))  # Cap at 2% of population
            cleaned['active'] = conservative_active
            print(f"DEBUG: {cleaned['name']} - Used conservative active: {conservative_active} (raw was {raw_active})")
        else:
            # Recovery data looks realistic, use it
            cleaned['active'] = raw_active
        
        # Calculated fields
        cleaned['infection_rate'] = self.calculate_infection_rate(cleaned['active'], cleaned['population'])
        cleaned['mortality_rate'] = self.calculate_mortality_rate(cleaned['deaths'], cleaned['cases'])
        cleaned['recovery_rate'] = self.calculate_recovery_rate(cleaned['recovered'], cleaned['cases'])
        cleaned['risk_level'] = self.get_risk_level(cleaned['infection_rate'])
        cleaned['marker_color'] = self.get_marker_color(cleaned['infection_rate'])
        
        # Formatted numbers for display
        cleaned['cases_formatted'] = self.format_number(cleaned['cases'])
        cleaned['deaths_formatted'] = self.format_number(cleaned['deaths'])
        cleaned['recovered_formatted'] = self.format_number(cleaned['recovered'])
        cleaned['population_formatted'] = self.format_number(cleaned['population'])

        if cleaned['estimation']:
            cleaned['estimation_formatted'] =  self.format_number(cleaned['estimation'])
        
        # Additional display fields
        cleaned['cases_per_100k'] = cleaned['infection_rate']  # Alias for clarity
        
        # Add type-specific styling
        if cleaned['type'] == 'country':
            cleaned['marker_size_multiplier'] = 1.5  # Larger markers for countries
            cleaned['display_name'] = f"🌍 {cleaned['name']}"
        elif cleaned['type'] == 'state':
            cleaned['marker_size_multiplier'] = 1.2  # Medium markers for states
            cleaned['display_name'] = f"🏛️ {cleaned['display_name']}"
        else:  # city
            cleaned['marker_size_multiplier'] = 1.0  # Normal size for cities
            cleaned['display_name'] = f"🏙️ {cleaned['display_name']}"
        
        # Timestamp
        cleaned['last_updated'] = location_data.get('last_updated', datetime.now().isoformat())
        
        return cleaned
    
    def process_cities_data(self, raw_cities_data: List[Dict]) -> List[Dict]:
        #Returns list of city data dicts

        if not raw_cities_data:
            logger.warning("No cities data provided for processing")
            return []
        
        processed_cities = []

        for city_data in raw_cities_data:
            try:
                cleaned_city = self.clean_city_data(city_data)

                if self.validate_city_data(cleaned_city):
                    processed_cities.append(cleaned_city)
                else:
                    logger.warning(f"Invalid city data for {city_data.get('name', 'Unknown')}")
            
            except Exception as e:
                logger.error(f"Error processing city data for {city_data.get('name', 'Unknown')}: {e}")
                continue

        processed_cities.sort(key=lambda x: x['infection_rate'], reverse=True)

        logger.info(f"Successfully processed {len(processed_cities)} cities")
        self.processed_data = processed_cities
        self.last_processed = datetime.now().isoformat()

        return processed_cities
    
    def validate_city_data(self, city_data: Dict) -> bool:
        
        required_fields = [
            'name', 'country', 'latitude', 'longitude', 
            'population', 'cases', 'infection_rate'
        ]
        
        if not all(field in city_data for field in required_fields):
            return False
        
        try:
            lat = float(city_data['latitude'])
            lon = float(city_data['longitude'])

            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return False
            
            if city_data['population'] <= 0 or city_data['cases'] < 0:
                return False
            
            return True
        
        except (ValueError, TypeError):
            return False
        
    def get_statistics_summary(self, cities_data: List[Dict]) -> Dict:
        #Returns stats summary dict
        if not cities_data:
            return {
                'total_cities': 0,
                'total_cases': 0,
                'total_deaths': 0,
                'total_recovered': 0,
                'average_infection_rate': 0,
                'highest_infection_rate': 0,
                'lowest_infection_rate': 0,
                'risk_distribution': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
            }
        
        total_cases = sum(city['cases'] for city in cities_data)
        total_deaths = sum(city['deaths'] for city in cities_data)
        total_recovered = sum(city['recovered'] for city in cities_data)

        infection_rates = [city['infection_rate'] for city in cities_data]
        avg_infection_rate = sum(infection_rates) / len(infection_rates)

        risk_distribution = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for city in cities_data:
            risk_level = city['risk_level']
            risk_distribution[risk_level] += 1
        
        return {
            'total_cities': len(cities_data),
            'total_cases': total_cases,
            'total_deaths': total_deaths,
            'total_recovered': total_recovered,
            'total_cases_formatted': self.format_number(total_cases),
            'total_deaths_formatted': self.format_number(total_deaths),
            'total_recovered_formatted': self.format_number(total_recovered),
            'average_infection_rate': round(avg_infection_rate, 2),
            'highest_infection_rate': max(infection_rates),
            'lowest_infection_rate': min(infection_rates),
            'risk_distribution': risk_distribution,
            'generated_at': datetime.now().isoformat()
        }
    
    def format_for_fronted(self, cities_data: List[Dict]) -> Dict:
        #Returns frontend data dict format

        return {
            'cities': cities_data,
            'statistics': self.get_statistics_summary(cities_data),
            'metadata': {
                'total_cities': len(cities_data),
                'last_updated': self.last_processed or datetime.now().isoformat(),
                'data_source': 'disease.sh API',
                'update_frequency': '24 hours'
            }
        }
    
    def filter_cities_by_risk(self, cities_data: List[Dict], risk_levels: List[str]) -> List[Dict]:
        #Returns filtered list of cities

        return [city for city in cities_data if city['risk_level'] in risk_levels]
    
    def get_top_cities_by_case(self, cities_data: List[Dict], limit: int = 10) -> List[Dict]:
        #Returns cities sorted by cases

        sorted_cities = sorted(cities_data, key=lambda x: x['cases'], reverse=True)
        return sorted_cities[:limit]
    
#Convenience funcs
def process_covid_data(raw_cities_data: List[Dict]) -> List[Dict]:
    processor = DataProcessor()
    return processor.process_cities_data(raw_cities_data)

def format_for_map(raw_cities_data: List[Dict]) -> Dict:
    processor = DataProcessor()
    processed_data = processor.process_cities_data(raw_cities_data)
    return processor.format_for_fronted(processed_data)