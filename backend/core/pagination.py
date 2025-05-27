"""
Advanced pagination classes for MigrateIQ API.

This module provides:
- Cursor-based pagination for large datasets
- Enhanced page number pagination
- Performance optimized pagination
- Metadata-rich pagination responses
"""

import base64
import json
from typing import Any, Dict, Optional, OrderedDict
from urllib.parse import urlencode

from django.core.paginator import Paginator, InvalidPage
from django.db import models
from django.utils.encoding import force_str
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param


class EnhancedPageNumberPagination(PageNumberPagination):
    """Enhanced page number pagination with additional metadata."""
    
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """Return paginated response with enhanced metadata."""
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('has_next', self.page.has_next()),
            ('has_previous', self.page.has_previous()),
            ('start_index', self.page.start_index()),
            ('end_index', self.page.end_index()),
            ('results', data)
        ]))
    
    def get_paginated_response_schema(self, schema):
        """Return schema for paginated response."""
        return {
            'type': 'object',
            'properties': {
                'count': {
                    'type': 'integer',
                    'description': 'Total number of items'
                },
                'total_pages': {
                    'type': 'integer',
                    'description': 'Total number of pages'
                },
                'current_page': {
                    'type': 'integer',
                    'description': 'Current page number'
                },
                'page_size': {
                    'type': 'integer',
                    'description': 'Number of items per page'
                },
                'next': {
                    'type': 'string',
                    'nullable': True,
                    'format': 'uri',
                    'description': 'URL to next page'
                },
                'previous': {
                    'type': 'string',
                    'nullable': True,
                    'format': 'uri',
                    'description': 'URL to previous page'
                },
                'has_next': {
                    'type': 'boolean',
                    'description': 'Whether there is a next page'
                },
                'has_previous': {
                    'type': 'boolean',
                    'description': 'Whether there is a previous page'
                },
                'start_index': {
                    'type': 'integer',
                    'description': 'Start index of current page items'
                },
                'end_index': {
                    'type': 'integer',
                    'description': 'End index of current page items'
                },
                'results': schema,
            },
        }


class OptimizedCursorPagination(CursorPagination):
    """Optimized cursor pagination for large datasets."""
    
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    cursor_query_param = 'cursor'
    ordering = '-created_at'  # Default ordering
    
    def __init__(self):
        super().__init__()
        self.template = 'rest_framework/pagination/cursor.html'
    
    def get_paginated_response(self, data):
        """Return cursor paginated response with metadata."""
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_size', self.get_page_size(self.request)),
            ('has_next', self.has_next),
            ('has_previous', self.has_previous),
            ('results', data)
        ]))
    
    def paginate_queryset(self, queryset, request, view=None):
        """Paginate queryset with performance optimizations."""
        self.page_size = self.get_page_size(request)
        if not self.page_size:
            return None
        
        self.base_url = request.build_absolute_uri()
        self.ordering = self.get_ordering(request, queryset, view)
        
        # Apply select_related and prefetch_related if available
        if hasattr(view, 'get_optimized_queryset'):
            queryset = view.get_optimized_queryset(queryset)
        
        cursor = self.decode_cursor(request)
        if cursor is None:
            (offset, reverse, current_position) = (0, False, None)
        else:
            (offset, reverse, current_position) = cursor
        
        # Cursor pagination implementation
        if reverse:
            queryset = queryset.order_by(*self._get_reversed_ordering())
        else:
            queryset = queryset.order_by(*self.ordering)
        
        if current_position is not None:
            order = self.ordering[0]
            is_reversed = order.startswith('-')
            order_attr = order.lstrip('-')
            
            # Build filter for cursor position
            if reverse != is_reversed:
                kwargs = {order_attr + '__lt': current_position}
            else:
                kwargs = {order_attr + '__gt': current_position}
            
            queryset = queryset.filter(**kwargs)
        
        # Get one extra item to determine if there are more pages
        results = list(queryset[offset:offset + self.page_size + 1])
        
        self.page = list(results[:self.page_size])
        
        # Determine if there are next/previous pages
        if reverse:
            self.has_next = (current_position is not None) or (offset > 0)
            self.has_previous = len(results) > len(self.page)
        else:
            self.has_next = len(results) > len(self.page)
            self.has_previous = (current_position is not None) or (offset > 0)
        
        if reverse:
            self.page = list(reversed(self.page))
        
        return self.page
    
    def _get_reversed_ordering(self):
        """Get reversed ordering for pagination."""
        result = []
        for order in self.ordering:
            if order.startswith('-'):
                result.append(order[1:])
            else:
                result.append('-' + order)
        return result


class SmartPagination:
    """Smart pagination that chooses the best pagination strategy."""
    
    def __init__(self, queryset, request, view=None):
        self.queryset = queryset
        self.request = request
        self.view = view
        self.count_threshold = 10000  # Switch to cursor pagination for large datasets
    
    def get_paginator(self):
        """Get the appropriate paginator based on dataset size."""
        # Check if we should use cursor pagination
        use_cursor = self.request.query_params.get('use_cursor', 'false').lower() == 'true'
        
        if use_cursor:
            return OptimizedCursorPagination()
        
        # For large datasets, recommend cursor pagination
        try:
            count = self.queryset.count()
            if count > self.count_threshold:
                # Add header suggesting cursor pagination
                response_headers = getattr(self.request, '_response_headers', {})
                response_headers['X-Pagination-Suggestion'] = 'cursor'
                response_headers['X-Total-Count'] = str(count)
        except Exception:
            # If count fails, use cursor pagination
            return OptimizedCursorPagination()
        
        return EnhancedPageNumberPagination()


class FilteredPagination(EnhancedPageNumberPagination):
    """Pagination with built-in filtering support."""
    
    def paginate_queryset(self, queryset, request, view=None):
        """Paginate queryset with filtering applied."""
        # Apply filters before pagination
        if hasattr(view, 'filter_queryset'):
            queryset = view.filter_queryset(queryset)
        
        return super().paginate_queryset(queryset, request, view)
    
    def get_paginated_response(self, data):
        """Return response with filter information."""
        response_data = super().get_paginated_response(data).data
        
        # Add filter information
        if hasattr(self.request, 'query_params'):
            filters_applied = {}
            for key, value in self.request.query_params.items():
                if key not in ['page', 'page_size', 'ordering']:
                    filters_applied[key] = value
            
            if filters_applied:
                response_data['filters_applied'] = filters_applied
        
        return Response(response_data)


class CachedPagination(EnhancedPageNumberPagination):
    """Pagination with caching support for expensive queries."""
    
    def __init__(self):
        super().__init__()
        self.cache_timeout = 300  # 5 minutes
    
    def paginate_queryset(self, queryset, request, view=None):
        """Paginate with caching for count queries."""
        from django.core.cache import cache
        from core.cache import cache_manager
        
        # Generate cache key for count
        cache_key = cache_manager.generate_cache_key(
            'pagination_count',
            str(queryset.query),
            request.user.id if request.user.is_authenticated else 'anonymous'
        )
        
        # Try to get count from cache
        cached_count = cache.get(cache_key)
        
        if cached_count is not None:
            # Use cached count to avoid expensive count query
            self._cached_count = cached_count
        
        result = super().paginate_queryset(queryset, request, view)
        
        # Cache the count if we computed it
        if not hasattr(self, '_cached_count') and hasattr(self, 'page'):
            count = self.page.paginator.count
            cache.set(cache_key, count, self.cache_timeout)
        
        return result


class AsyncPagination(EnhancedPageNumberPagination):
    """Pagination optimized for async operations."""
    
    async def apaginate_queryset(self, queryset, request, view=None):
        """Async version of paginate_queryset."""
        # This would be implemented when Django adds async ORM support
        # For now, this is a placeholder for future async functionality
        return self.paginate_queryset(queryset, request, view)
    
    def get_paginated_response(self, data):
        """Return response with async metadata."""
        response_data = super().get_paginated_response(data).data
        response_data['async_supported'] = True
        return Response(response_data)


# Utility functions for pagination
def get_pagination_class(request, queryset_size=None):
    """Get the best pagination class for the request."""
    # Check for explicit pagination type
    pagination_type = request.query_params.get('pagination_type', 'page')
    
    if pagination_type == 'cursor':
        return OptimizedCursorPagination
    elif pagination_type == 'filtered':
        return FilteredPagination
    elif pagination_type == 'cached':
        return CachedPagination
    else:
        # Default to enhanced page pagination
        return EnhancedPageNumberPagination


def paginate_queryset(queryset, request, view=None, pagination_class=None):
    """Utility function to paginate any queryset."""
    if pagination_class is None:
        pagination_class = get_pagination_class(request)
    
    paginator = pagination_class()
    return paginator.paginate_queryset(queryset, request, view)
