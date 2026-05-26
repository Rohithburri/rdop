import json
import math
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST


# Your pickup location coordinates
# Example: Hyderabad coordinates
# Replace these with your real pickup/shop/warehouse latitude and longitude
PICKUP_LATITUDE = 17.437462
PICKUP_LONGITUDE = 78.400688

MAX_DELIVERY_DISTANCE_KM = 10


def location_page(request):
    return render(request, "locationcheck/location.html")


def next_step(request):
    location_allowed = request.session.get("location_allowed", False)

    if not location_allowed:
        return render(request, "locationcheck/location.html", {
            "error": "Please allow location access first."
        })

    return render(request, "locationcheck/next_step.html")


def calculate_distance_km(lat1, lon1, lat2, lon2):
    """
    Haversine formula to calculate distance between two coordinates.
    Returns distance in kilometers.
    """

    earth_radius_km = 6371

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    difference_lat = lat2_rad - lat1_rad
    difference_lon = lon2_rad - lon1_rad

    a = (
        math.sin(difference_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(difference_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = earth_radius_km * c
    return distance


@require_POST
def check_location(request):
    try:
        data = json.loads(request.body)

        customer_latitude = float(data.get("latitude"))
        customer_longitude = float(data.get("longitude"))

        distance_km = calculate_distance_km(
            PICKUP_LATITUDE,
            PICKUP_LONGITUDE,
            customer_latitude,
            customer_longitude
        )

        distance_km = round(distance_km, 2)

        if distance_km <= MAX_DELIVERY_DISTANCE_KM:
            request.session["location_allowed"] = True
            request.session["customer_latitude"] = customer_latitude
            request.session["customer_longitude"] = customer_longitude
            request.session["distance_km"] = distance_km

            return JsonResponse({
                "success": True,
                "deliverable": True,
                "distance_km": distance_km,
                "message": "Delivery available to your location."
            })

        else:
            request.session["location_allowed"] = False

            return JsonResponse({
                "success": True,
                "deliverable": False,
                "distance_km": distance_km,
                "message": "Sorry, delivery is not available to your location."
            })

    except Exception as error:
        return JsonResponse({
            "success": False,
            "message": "Unable to check your location.",
            "error": str(error)
        }, status=400)