import pytest
from app.internal.route_service import optimize_routes_service

def test_optimize_routes_service():
    """
    Test basique de l'intégration du service d'optimisation.
    Vérifie que la réponse contient les clés attendues.
    """
    response = optimize_routes_service()
    assert isinstance(response, dict)
    assert "optimized_routes" in response
    assert "total_cost" in response
    assert "meta" in response
    print("Réponse du service :", response)
