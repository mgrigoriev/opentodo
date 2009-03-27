from django.conf import settings

def host(request):    
    return {'HOST': request.get_host()}

def my_media_url(request):
    my_media_url = settings.MEDIA_URL
    if not my_media_url.endswith('/'):
        my_media_url += '/'
    return {'MEDIA_URL': my_media_url}