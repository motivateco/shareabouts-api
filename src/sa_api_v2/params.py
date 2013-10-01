from django.conf import settings

# Querystring Parameter Names
INCLUDE_INVISIBLE_PARAM = 'include_invisible'
INCLUDE_PRIVATE_PARAM = 'include_private'
INCLUDE_SUBMISSIONS_PARAM = 'include_submissions'
NEAR_PARAM = 'near'
FORMAT_PARAM = 'format'

PAGE_PARAM = 'page'
PAGE_SIZE_PARAM = lambda: getattr(settings, 'REST_FRAMEWORK', {}).get('PAGINATE_BY_PARAM')