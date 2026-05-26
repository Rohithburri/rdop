import json
import math

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie


# Pickup location coordinates
# Madhapur Metro Station
PICKUP_LATITUDE = 17.437462
PICKUP_LONGITUDE = 78.400688

MAX_DELIVERY_DISTANCE_KM = 10


@require_GET
@ensure_csrf_cookie
def location_page(request):
    """
    Shows the first page and sets CSRF cookie.
    This is important because frontend JavaScript sends POST request later.
    """
    return render(request, "locationcheck/location.html")


@require_GET
def next_step(request):
    """
    Shows next page only if customer location is verified and deliverable.
    """
    location_allowed = request.session.get("location_allowed", False)

    if not location_allowed:
        return render(request, "locationcheck/location.html", {
            "error": "Please allow location access first."
        })

    distance_km = request.session.get("distance_km")

    return render(request, "locationcheck/next_step.html", {
        "distance_km": distance_km
    })


def calculate_distance_km(lat1, lon1, lat2, lon2):
    """
    Haversine formula.
    Calculates distance between pickup location and customer location.
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
    """
    Receives customer latitude and longitude from frontend.
    Checks whether customer is within 10 km delivery range.
    """

    try:
        data = json.loads(request.body)

        customer_latitude = data.get("latitude")
        customer_longitude = data.get("longitude")

        if customer_latitude is None or customer_longitude is None:
            return JsonResponse({
                "success": False,
                "message": "Latitude and longitude are required."
            }, status=400)

        customer_latitude = float(customer_latitude)
        customer_longitude = float(customer_longitude)

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

        request.session["location_allowed"] = False
        request.session["customer_latitude"] = customer_latitude
        request.session["customer_longitude"] = customer_longitude
        request.session["distance_km"] = distance_km

        return JsonResponse({
            "success": True,
            "deliverable": False,
            "distance_km": distance_km,
            "message": "Sorry, delivery is not available to your location."
        })

    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid JSON data."
        }, status=400)

    except ValueError:
        return JsonResponse({
            "success": False,
            "message": "Invalid latitude or longitude."
        }, status=400)

    except Exception as error:
        return JsonResponse({
            "success": False,
            "message": "Unable to check your location.",
            "error": str(error)
        }, status=400)