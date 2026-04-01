from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import traceback

def custom_exception_handler(exc, context):
    """
    Custom exception handler that catches unhandled 500 errors, 
    prints the traceback, and returns a JSON response.
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # If response is None, then there was an unhandled exception (500)
    if response is None:
        import logging
        logger = logging.getLogger('django')
        logger.error(f"Unhandled Exception in {context['view'].__class__.__name__}:")
        logger.error(traceback.format_exc())
        
        return Response({
            'error': 'Internal Server Error',
            'detail': str(exc),
            'type': exc.__class__.__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
