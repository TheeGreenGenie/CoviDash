# 🦠 COVID-19 Global Tracker

An interactive, real-time COVID-19 tracking dashboard with a dark-themed world map, providing comprehensive pandemic data visualization for major cities worldwide.

## 🌐 Live Demo

### **🚀 [View Live Application](https://covidash.onrender.com) 🚀**

*Experience the full interactive dashboard with real-time COVID-19 data from around the world.*

## 📸 Features

### 🗺️ Interactive World Map
- **Dark-themed** Leaflet.js map optimized for extended viewing
- **Color-coded markers** representing risk levels (Low → Critical)
- **Multi-location support**: Cities, US States, and Countries
- **Responsive markers** that scale based on infection rates
- **Detailed popups** with comprehensive COVID statistics

### 📊 Real-Time Data
- **Automatic updates** every 24 hours
- **Multiple data sources**: disease.sh API (Johns Hopkins CSSE) + CDC
- **Smart data processing** with estimation algorithms for missing recovery data
- **Comprehensive caching** system for optimal performance

### 📈 Analytics & Statistics
- **Global statistics** dashboard with real-time totals
- **Risk distribution** charts showing city categorization
- **Infection rate** calculations per 100k population
- **Mortality and recovery** rate tracking with smart estimation
- **Interactive statistics** panel with detailed breakdowns

### 🎨 Modern UI/UX
- **Professional dark theme** with carefully crafted color palette
- **Fully responsive design** for desktop, tablet, and mobile devices
- **Smooth animations** and interactive hover effects
- **Accessibility features** with proper contrast and semantic markup
- **Loading states** and comprehensive error handling
- **Custom map controls** and status indicators

### 🔧 Advanced Features
- **Smart data estimation** algorithms for missing recovery data
- **Multi-source data validation** and cross-referencing
- **Automatic fallback systems** when primary data sources are unavailable
- **Real-time health monitoring** of application components
- **Performance optimization** with intelligent caching strategies

## 🛠️ Tech Stack

### Backend
- **Flask** - Lightweight Python web framework
- **Flask-APScheduler** - Automated data refresh scheduling
- **Requests** - HTTP library for API calls
- **Python 3.9+** - Core runtime

### Frontend
- **Leaflet.js** - Interactive map library
- **Vanilla JavaScript** - No heavy frameworks, pure performance
- **CSS Grid & Flexbox** - Modern responsive layouts
- **CSS Custom Properties** - Maintainable theming system

### Data Sources
- **disease.sh API** - Primary COVID data source (Johns Hopkins CSSE)
- **CDC Open Data** - Secondary official data source
- **Custom algorithms** - Smart data estimation and processing

### Infrastructure
- **Render.com** - Cloud hosting platform
- **Gunicorn** - Production WSGI server
- **Multi-layer caching** - Memory + file-based caching system

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/covid-tracker.git
cd covid-tracker
```

2. **Create virtual environment**
```bash
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
# Create .env file
cp .env.example .env

# Edit .env with your preferences
FLASK_ENV=development
FLASK_DEBUG=True
UPDATE_INTERVAL_HOURS=24
```

5. **Run the application**
```bash
python app.py
```

6. **Open your browser**
Navigate to `http://localhost:5000`

## 📋 Project Structure

```
covid-tracker/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── data/
│   ├── __init__.py
│   ├── fetcher.py             # Data fetching from APIs
│   ├── processor.py           # Data cleaning and processing
│   └── cache.py               # Caching system
├── templates/
│   ├── base.html              # Base HTML template
│   └── index.html             # Main page template
├── static/
│   ├── css/
│   │   └── styles.css         # Dark theme CSS
│   ├── js/
│   │   ├── map.js             # Leaflet map functionality
│   │   └── api.js             # API communication
│   └── images/
│       └── favicon.ico
├── utils/
│   ├── __init__.py
│   └── scheduler.py           # Background task scheduling
└── deployment/
    ├── render.yaml            # Render deployment config
    └── freeze.py              # Static site generation script
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `development` |
| `FLASK_DEBUG` | Debug mode | `False` |
| `UPDATE_INTERVAL_HOURS` | Data refresh interval | `24` |
| `CDC_API_BASE` | CDC API base URL | `https://data.cdc.gov/resource` |
| `DISEASE_SH_API` | disease.sh API base URL | `https://disease.sh/v3/covid-19` |

### Risk Level Thresholds

- **Low**: < 500 cases per 100k population
- **Medium**: 500-2000 cases per 100k
- **High**: 2000-5000 cases per 100k  
- **Critical**: > 5000 cases per 100k

## 📡 API Endpoints

### Public Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/` | GET | Main dashboard |
| `/api/covid-data` | GET | COVID data for map |
| `/api/statistics` | GET | Global statistics |
| `/api/health` | GET | Application health status |

### Admin Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/refresh` | POST | Manual data refresh |
| `/api/cache/info` | GET | Cache information |
| `/api/cache/clear` | POST | Clear cache |

## 🏗️ Architecture

### Data Flow
1. **Scheduled Jobs** fetch data from multiple APIs every 24 hours
2. **Data Processor** cleans, validates, and enhances raw data
3. **Caching Layer** stores processed data for fast retrieval
4. **Flask API** serves data to the frontend
5. **Interactive Map** renders real-time visualizations

### Performance Optimizations
- **Intelligent Caching**: Multi-layer caching reduces API calls
- **Data Compression**: Efficient data structures minimize bandwidth
- **Lazy Loading**: Components load as needed
- **Error Resilience**: Graceful fallbacks when APIs are unavailable

## 🧪 Development

### Running Tests
```bash
python -m pytest tests/
```

### Data Sources Testing
```bash
# Test API connectivity
python -c "from data.fetcher import DataFetcher; fetcher = DataFetcher('https://disease.sh/v3/covid-19', ''); print(fetcher.get_data_summary())"
```

### Local Development Features
- **Hot reload** enabled in development mode
- **Debug toolbar** for performance monitoring
- **Detailed logging** for troubleshooting
- **Cache management** tools via API endpoints

## 📊 Data Processing

### Smart Estimation Algorithm
The application includes sophisticated data processing:

1. **Missing Recovery Data Handling**: Estimates recovery rates based on global patterns
2. **Population-Based Scaling**: Calculates city-level data from country/state statistics  
3. **Realistic Constraints**: Applies bounds to prevent unrealistic infection rates
4. **Multi-Source Validation**: Cross-references CDC and disease.sh data

### Caching Strategy
- **Memory Cache**: Fast access for frequent requests
- **File Cache**: Persistent storage with 24-hour TTL
- **Auto-Cleanup**: Removes expired entries automatically
- **Graceful Degradation**: Falls back to cached data if APIs are unavailable

## 🙏 Credits & Data Sources

### Data Providers
- **[disease.sh](https://disease.sh/)** - Primary COVID-19 data aggregation service
  - Sources: Johns Hopkins CSSE, Worldometers, Apple reports, government sources
  - License: Open source, free to use
- **[Centers for Disease Control and Prevention (CDC)](https://data.cdc.gov/)** - Official US health data
  - COVID-19 case surveillance and epidemiological data
  - Public domain government data
- **[Johns Hopkins University CSSE](https://github.com/CSSEGISandData/COVID-19)** - Original COVID-19 data repository
  - Comprehensive global time series data
  - Open data for research and public use

### Mapping & Visualization
- **[Leaflet.js](https://leafletjs.com/)** - Open-source JavaScript library for interactive maps
  - License: BSD 2-Clause License
- **[CartoDB](https://carto.com/)** - Dark theme map tiles
  - Basemap data © OpenStreetMap contributors
- **[OpenStreetMap](https://www.openstreetmap.org/)** - Fallback map tiles and geographic data
  - License: Open Database License (ODbL)

### Backend Technologies
- **[Flask](https://flask.palletsprojects.com/)** - Python web framework
  - License: BSD 3-Clause License
- **[Flask-APScheduler](https://github.com/viniciuschiele/flask-apscheduler)** - Background job scheduling
- **[Requests](https://docs.python-requests.org/)** - HTTP library for Python
- **[Gunicorn](https://gunicorn.org/)** - Python WSGI HTTP Server

### Hosting & Infrastructure
- **[Render](https://render.com/)** - Cloud application hosting platform
- Application deployed at: **[covidash.onrender.com](https://covidash.onrender.com)**

### Design Inspiration
- Dark theme color palette inspired by GitHub Dark and VS Code Dark themes
- Risk level color scheme based on epidemiological standards
- UI/UX patterns following modern web accessibility guidelines

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

### Data Usage Disclaimer
- **Educational Purpose**: This application is created for educational and informational purposes only
- **Not for Medical Decisions**: Data should not be used for medical diagnosis or treatment decisions
- **Data Accuracy**: While we strive for accuracy, data may have delays or inconsistencies
- **Consult Authorities**: Always refer to official health authorities for medical guidance

### Privacy & Data Handling
- **No Personal Data Collection**: This application does not collect or store personal user data
- **Third-party APIs**: Data is fetched from public APIs with proper rate limiting and caching
- **Local Storage**: Only temporary caching for performance optimization