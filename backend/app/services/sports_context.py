from typing import Optional
from fastapi import Request

class SportsContext:
    """
    Service for managing sports context across requests.
    This helps maintain consistency in sport selection across different pages and API calls.
    """
    def __init__(self):
        self._default_sport = "NBA"
        
    def get_active_sport(self, request: Optional[Request] = None) -> str:
        """
        Get the currently active sport from the request or use the default.
        In a real implementation, this could check headers, cookies, or query params.
        """
        if request is None:
            return self._default_sport
        
        # Check if sport is in the query parameters
        sport = request.query_params.get("sport")
        if sport:
            return sport.upper()
        
        # In a more complex implementation, could check cookies or other storage
        return self._default_sport
    
    def set_default_sport(self, sport: str) -> None:
        """Set the default sport to use when none is specified"""
        self._default_sport = sport.upper()
    
    def get_available_sports(self) -> list[str]:
        """Get list of available sports"""
        return ["NBA", "NFL", "EPL"]

# Create a singleton instance
sports_context = SportsContext()

def get_sports_context() -> SportsContext:
    """Dependency to inject the sports context service"""
    return sports_context