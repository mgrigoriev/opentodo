def site_media_url(request):
    from django.conf import settings
    return {'MEDIA_URL': settings.MEDIA_URL, 'HOST': request.get_host()}
#    return {
#		'SITE_MEDIA_URL': settings.SITE_MEDIA_URL,
#		'PROJECT_PATH': settings.PROJECT_PATH,
#		'MEDIA_URL': settings.MEDIA_URL}