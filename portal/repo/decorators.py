
from functools import wraps
from django.http import HttpResponseRedirect
from django.utils.decorators import available_attrs


def user_passes_test(test_func):
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            return HttpResponseRedirect("/login/")
        return _wrapped_view
    return decorator


def aso_login_required(function=None):
    actual_decorator = user_passes_test(lambda u: u.is_authenticated())
    if function:
        return actual_decorator(function)
    return actual_decorator