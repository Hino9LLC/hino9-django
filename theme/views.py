from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def handler404(request: HttpRequest, exception: Exception) -> HttpResponse:
    """
    Custom 404 error handler.
    Only used when DEBUG=False in production.
    """
    return render(
        request,
        "404.html",
        {
            "exception": exception,
        },
        status=404,
    )


def handler500(request: HttpRequest) -> HttpResponse:
    """
    Custom 500 error handler.
    Only used when DEBUG=False in production.
    Note: In 500 errors, context may be limited to avoid additional errors.
    """
    return render(request, "500.html", status=500)
