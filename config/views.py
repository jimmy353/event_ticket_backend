from django.http import JsonResponse

def home(request):
    return JsonResponse({
        "message": "Sirheart Events Backend is Live 🚀",
        "status": "ok"
    })