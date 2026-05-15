class APIVersionMiddleware:
    """
    Middleware para añadir la cabecera X-API-Version a todas las respuestas de la API.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Si la URL empieza con /api/, intentamos extraer la versión
        if request.path.startswith('/api/'):
            # El versionado de DRF ya lo extrajo si se configuró URLPathVersioning
            version = getattr(request, 'version', None)
            
            # Fallback manual por si acaso
            if not version:
                import re
                match = re.search(r'/api/(v\d+)/', request.path)
                version = match.group(1) if match else 'v1'
                
            response['X-API-Version'] = version
            
        return response
