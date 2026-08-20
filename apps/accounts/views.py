from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def profile_view(request):
    """
    Simple post-login landing page (LOGIN_REDIRECT_URL = account:profile).
    Later phases will list the buyer's purchased books and download history here.
    """
    context = {
        "user": request.user,
        "orders": request.user.orders.all()[:5] if hasattr(request.user, "orders") else [],
    }
    return render(request, "accounts/profile.html", context)
