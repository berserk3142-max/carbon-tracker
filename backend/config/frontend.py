"""
Serve the built Vite frontend from Django for single-container deployments.
"""
from mimetypes import guess_type

from django.conf import settings
from django.http import FileResponse, Http404


def frontend_app(request, path=''):
    frontend_dist = settings.FRONTEND_DIST.resolve()
    requested_path = (frontend_dist / path).resolve()

    if not requested_path.is_relative_to(frontend_dist):
        raise Http404('File not found')

    if path and requested_path.is_file():
        content_type, _ = guess_type(str(requested_path))
        return FileResponse(requested_path.open('rb'), content_type=content_type)

    index_path = frontend_dist / 'index.html'
    if index_path.is_file():
        return FileResponse(index_path.open('rb'), content_type='text/html')

    raise Http404('Frontend build not found')
