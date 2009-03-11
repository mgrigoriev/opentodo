def host(request):
    from django.conf import settings
    return {'HOST': request.get_host()}