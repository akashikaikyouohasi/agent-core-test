from strands import  tool

def get_tools() -> list:
    """Return a list of tools including weather-related tools."""
    return [get_user_location, weather]

@tool
def get_user_location() -> str:
    """
    Get the user's location.
    Returns:
        str: The user's location (e.g., city name)
    """
    return "Tokyo"

@tool
def weather(location: str) -> str:
    """
    Get the current weather for a given location.
    Args:
        location (str): The location to get the weather for
    Returns:
        str: The current weather description
    """
    return f"Weather for {location}: Sunny, 25°C".format(location=location)

