from functools import wraps
from django.shortcuts import redirect


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/admin/login/?next={request.path}")
        if not request.user.is_staff:
            return redirect("/")
        return view_func(request, *args, **kwargs)
    return _wrapped
