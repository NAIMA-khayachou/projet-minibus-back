# app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OSRM Configuration
    OSRM_BASE_URL: str = "http://localhost:5000"
    OSRM_TIMEOUT: int = 30
    OSRM_PROFILE: str = "driving"
    
    # Genetic Algorithm Parameters
    GA_POPULATION_SIZE: int = 100
    GA_MAX_GENERATIONS: int = 200
    GA_MUTATION_RATE: float = 0.15
    GA_CROSSOVER_RATE: float = 0.80
    GA_ELITISM_RATE: float = 0.10
    GA_TOURNAMENT_SIZE: int = 5
    GA_CONVERGENCE_THRESHOLD: int = 50
    
    # Penalties
    CAPACITY_VIOLATION_PENALTY: float = 10000.0
    TIME_WINDOW_VIOLATION_PENALTY: float = 5000.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()