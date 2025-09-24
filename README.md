# Scoracle - Sports News & Statistics Platform

Scoracle is a modern web application that serves as a one-stop shop for sports enthusiasts to get the latest news and statistical information about their favorite players and teams.

## Features

- Search for players and teams across multiple sports (NBA, NFL, EPL)
- View latest news mentions via Google RSS integration
- See detailed statistical information via sports APIs
- Interactive data visualizations using D3.js

## Tech Stack

### Backend
- FastAPI (Python)
- httpx for async API requests
- Integration with balldontlie.io API

### Frontend
- React 
- React Router for navigation
- Mantine UI components
- D3.js for data visualization
- Axios for API requests

## Getting Started

### Prerequisites
- Docker and Docker Compose (recommended)
- Node.js 16+ (for local frontend development)
- Python 3.8+ (for local backend development)

### Running with Docker

1. Clone the repository
```bash
git clone https://github.com/yourusername/scoracle.git
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

## API Routes

### Backend API

- `GET /api/v1/` - Get home page data
- `GET /api/v1/search` - Search for players or teams
- `GET /api/v1/mentions/{entity_type}/{entity_id}` - Get mentions for a player or team
- `GET /api/v1/players/{player_id}` - Get player details
- `GET /api/v1/teams/{team_id}` - Get team details

## Project Structure

```
scoracle/
├── backend/            # FastAPI backend
│   ├── app/            # Application code
│   │   ├── routers/    # API routes
│   │   ├── services/   # Service layer (API integrations)
│   │   └── models/     # Data models
├── frontend/           # React frontend
│   ├── public/         # Static files
│   └── src/            # Source code
│       ├── components/ # Reusable components
│       ├── pages/      # Page components
│       ├── services/   # API services
│       └── context/    # React context
└── docker-compose.yml  # Docker configuration
```

## Future Enhancements

- Add support for more sports leagues
- Implement user accounts and favorites
- Add historical statistics and trends
- Develop mobile app version
