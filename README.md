# Scoracle - Sports News & Statistics Platform

Scoracle is a modern web application that serves as a one-stop shop for sports enthusiasts to get the latest news and statistical information about their favorite players and teams across multiple leagues including NBA, NFL, and EPL.

## Features

- **Multi-sport Support**: Seamlessly switch between different sports (NBA, NFL, EPL) with a consistent UI
- **Entity Search**: Search for players and teams across all supported sports
- **News Aggregation**: View the latest news mentions from the past 36 hours via Google RSS integration
- **Detailed Statistics**: Access comprehensive player and team statistics via sports APIs
- **Interactive Visualizations**: Explore sports data through interactive D3.js visualizations
- **Responsive Design**: Enjoy a smooth experience across desktop and mobile devices

## Tech Stack

### Backend
- **FastAPI**: Modern, high-performance Python web framework
- **httpx**: Asynchronous HTTP client for API integration
- **balldontlie.io API**: Primary data source for NBA statistics
- **Google RSS**: News aggregation source

### Frontend
- **React**: Component-based UI library
- **React Router**: For application routing
- **Mantine UI**: Component library for consistent styling
- **D3.js**: Data visualization library
- **Axios**: HTTP client for API requests
- **Context API**: For managing application state

## Project Structure

```
scoracle/
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Data models and schemas
│   │   ├── routers/        # API routes
│   │   │   ├── home.py     # Home and search endpoints
│   │   │   ├── mentions.py # News mentions endpoints
│   │   │   ├── links.py    # Related links endpoints
│   │   │   ├── player.py   # Player statistics endpoints
│   │   │   └── team.py     # Team statistics endpoints
│   │   └── services/       # External API integrations
│   │       ├── balldontlie_api.py  # Sports data API service
│   │       ├── google_rss.py       # News RSS service
│   │       └── sports_context.py   # Sport selection service
│   ├── Dockerfile          # Backend container configuration
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── public/             # Static files
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── context/        # React context providers
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client services
│   │   └── visualizations/ # D3.js visualization components
│   ├── Dockerfile          # Frontend container configuration
│   └── package.json        # JavaScript dependencies
├── docker-compose.yml      # Multi-container Docker configuration
└── README.md               # Project documentation
```

## Getting Started

### Prerequisites
- Docker and Docker Compose (recommended)
- Node.js 16+ (for local frontend development)
- Python 3.8+ (for local backend development)

### Running with Docker

1. Clone the repository
```bash
git clone https://github.com/albapepper/scoracle.git
cd scoracle
```

2. Start the application
```bash
docker-compose up
```

3. Access the application at http://localhost:3000

### Development Setup

#### Backend (FastAPI)

1. Navigate to the backend directory
```bash
cd backend
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run the development server
```bash
uvicorn app.main:app --reload
```

5. Access the API documentation at http://localhost:8000/api/docs

### Local Development Quick Start (Copy/Paste)

These snippets let you spin up just what you need without Docker while iterating.

#### Backend (FastAPI) – Windows PowerShell

```powershell
cd backend
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Backend (macOS / Linux bash)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/api/docs

#### Frontend (React) – Windows PowerShell / macOS / Linux

```powershell
cd frontend
npm install
npm start
```

The React dev server proxies API calls to http://localhost:8000 via the `proxy` field in `frontend/package.json`.

#### One-Liner (already installed deps & venv exists)

PowerShell:
```powershell
cd backend; ./venv/Scripts/Activate.ps1; uvicorn app.main:app --reload --port 8000
```

macOS/Linux:
```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

#### Stopping Services
- Backend (Ctrl+C in the uvicorn terminal)
- Frontend (Ctrl+C in the React dev server terminal)
- Docker stack (if running): `docker-compose down`

#### Troubleshooting Quick Notes
- If imports fail after refactor, ensure the virtualenv is activated.
- Port already in use? Change with `--port 8001` (update frontend `proxy` if needed).
- If API key changes, expose it via an `.env` and load in `settings` (future enhancement).

#### Frontend (React)

1. Navigate to the frontend directory
```bash
cd frontend
```

2. Install dependencies
```bash
npm install
```

3. Run the development server
```bash
npm start
```

4. Access the frontend at http://localhost:3000

## API Documentation

### API Endpoints

#### Home Router
- `GET /api/v1/` - Get home page information and configuration
- `GET /api/v1/search` - Search for players or teams

#### Mentions Router
- `GET /api/v1/mentions/{entity_type}/{entity_id}` - Get mentions and basic information for a player or team

#### Links Router
- `GET /api/v1/links/{entity_type}/{entity_id}` - Get related links for a player or team

#### Player Router
- `GET /api/v1/player/{player_id}` - Get detailed player information and statistics
- `GET /api/v1/player/{player_id}/seasons` - Get list of seasons for which a player has statistics

#### Team Router
- `GET /api/v1/team/{team_id}` - Get detailed team information and statistics
- `GET /api/v1/team/{team_id}/roster` - Get roster of players for a team

### API Keys

The application uses the following API keys:
- **balldontlie.io API**: `fd8788ca-65fe-4ea6-896f-a2c9776977d1`

## Data Flow

1. User selects a sport from the header banner
2. User enters a player or team name in the search form
3. Backend searches for matching entities
4. User is redirected to the mentions page for the selected entity
5. Mentions page displays:
   - Basic entity information from the sports API
   - Recent news mentions from Google RSS
6. User can navigate to the detailed stats page
7. Stats page displays interactive D3.js visualizations of entity statistics

## Future Enhancements

- Add support for more sports leagues (MLB, NHL, etc.)
- Implement user accounts and favorites
- Add historical statistics and trends
- Develop mobile app version
- Add comparison features for players and teams
- Implement real-time score updates

## Deployment

- [Google Cloud Run guide](docs/deployment/cloud-run.md) — step-by-step instructions for publishing the frontend and backend using Artifact Registry and Cloud Run.

## License

This project is licensed under the MIT License.
