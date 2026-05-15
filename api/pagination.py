from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination

class EncomiendaPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 100

class ClientePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50

class HistorialPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 50

class EncomiendaCursorPagination(CursorPagination):
    page_size = 15
    ordering = '-fecha_registro'
