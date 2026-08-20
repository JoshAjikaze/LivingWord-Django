import base64
import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core import signing
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from .models import SocialAccount


PROVIDERS = {
    "facebook": {"authorize": "https://www.facebook.com/v23.0/dialog/oauth", "token": "https://graph.facebook.com/v23.0/oauth/access_token", "scopes": "pages_show_list,pages_manage_posts,pages_read_engagement"},
    "instagram": {"authorize": "https://www.facebook.com/v23.0/dialog/oauth", "token": "https://graph.facebook.com/v23.0/oauth/access_token", "scopes": "instagram_basic,instagram_content_publish,pages_read_engagement"},
    "threads": {"authorize": "https://threads.net/oauth/authorize", "token": "https://graph.threads.net/oauth/access_token", "scopes": "threads_basic,threads_content_publish"},
    "youtube": {"authorize": "https://accounts.google.com/o/oauth2/v2/auth", "token": "https://oauth2.googleapis.com/token", "scopes": "https://www.googleapis.com/auth/youtube.upload"},
    "x": {"authorize": "https://twitter.com/i/oauth2/authorize", "token": "https://api.x.com/2/oauth2/token", "scopes": "tweet.read tweet.write users.read offline.access"},
}


def _settings(platform):
    prefix = platform.upper()
    return getattr(settings, f"SOCIAL_{prefix}_CLIENT_ID", ""), getattr(settings, f"SOCIAL_{prefix}_CLIENT_SECRET", "")


def _redirect_uri(request, platform):
    base = getattr(settings, "SOCIAL_OAUTH_REDIRECT_BASE", "").rstrip("/") or request.build_absolute_uri("/").rstrip("/")
    return f"{base}{reverse('social:oauth_callback', kwargs={'platform': platform})}"


@staff_member_required
def oauth_start(request, platform):
    if platform not in PROVIDERS:
        return HttpResponseBadRequest("Unsupported platform.")
    client_id, _ = _settings(platform)
    if not client_id:
        messages.error(request, f"Configure SOCIAL_{platform.upper()}_CLIENT_ID before connecting this platform.")
        return redirect("admin:index")
    state_data = {"platform": platform, "nonce": secrets.token_urlsafe(24)}
    state = signing.dumps(state_data, salt="social-oauth")
    request.session[f"social_oauth_{state_data['nonce']}"] = state_data
    params = {"client_id": client_id, "redirect_uri": _redirect_uri(request, platform), "response_type": "code", "scope": PROVIDERS[platform]["scopes"], "state": state}
    if platform == "youtube":
        params.update({"access_type": "offline", "prompt": "consent"})
    if platform == "x":
        verifier = secrets.token_urlsafe(48)
        request.session[f"social_pkce_{state_data['nonce']}"] = verifier
        params["code_challenge"] = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        params["code_challenge_method"] = "S256"
    return redirect(f"{PROVIDERS[platform]['authorize']}?{urlencode(params)}")


@staff_member_required
def oauth_callback(request, platform):
    if platform not in PROVIDERS:
        return HttpResponseBadRequest("Unsupported platform.")
    if request.GET.get("error"):
        messages.error(request, f"{platform.title()} authorization was declined: {request.GET.get('error_description', request.GET['error'])}")
        return redirect("admin:index")
    try:
        state_data = signing.loads(request.GET.get("state", ""), salt="social-oauth", max_age=900)
    except signing.BadSignature:
        return HttpResponseBadRequest("Invalid or expired OAuth state.")
    client_id, client_secret = _settings(platform)
    payload = {"client_id": client_id, "client_secret": client_secret, "code": request.GET.get("code"), "grant_type": "authorization_code", "redirect_uri": _redirect_uri(request, platform)}
    if platform == "x":
        payload["code_verifier"] = request.session.get(f"social_pkce_{state_data['nonce']}", "")
    token_response = requests.post(PROVIDERS[platform]["token"], data=payload, timeout=60)
    if token_response.status_code >= 400:
        messages.error(request, f"{platform.title()} token exchange failed: {token_response.text[:500]}")
        return redirect("admin:index")
    token_data = token_response.json()
    access_token = token_data.get("access_token", "")
    if not access_token:
        return HttpResponseBadRequest("OAuth provider returned no access token.")
    identity = _identity(platform, access_token)
    SocialAccount.objects.update_or_create(
        platform=platform,
        external_id=identity["external_id"],
        defaults={
            "name": identity["name"],
            "access_token_ciphertext": SocialAccount.encrypt_token(access_token),
            "refresh_token_ciphertext": SocialAccount.encrypt_token(token_data.get("refresh_token", "")),
            "token_expires_at": timezone.now() + timedelta(seconds=int(token_data.get("expires_in", 5_184_000))),
            "metadata": identity.get("metadata", {}),
            "is_active": True,
            "connected_by": request.user,
        },
    )
    messages.success(request, f"Connected {identity['name']} to {platform.title()} publishing.")
    return redirect("admin:social_socialaccount_changelist")


def _identity(platform, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    if platform in {"facebook", "instagram"}:
        data = requests.get("https://graph.facebook.com/v23.0/me", params={"fields": "id,name", "access_token": access_token}, timeout=60).json()
        return {"external_id": data["id"], "name": data.get("name", data["id"]), "metadata": {"provider_user_id": data["id"]}}
    if platform == "threads":
        data = requests.get("https://graph.threads.net/v1.0/me", params={"fields": "id,username", "access_token": access_token}, timeout=60).json()
        return {"external_id": data["id"], "name": data.get("username", data["id"]), "metadata": {"username": data.get("username", "")}}
    if platform == "youtube":
        data = requests.get("https://www.googleapis.com/youtube/v3/channels", params={"part": "snippet", "mine": "true", "access_token": access_token}, timeout=60).json()["items"][0]
        return {"external_id": data["id"], "name": data["snippet"]["title"], "metadata": {"default_privacy": "private"}}
    data = requests.get("https://api.x.com/2/users/me", headers=headers, timeout=60).json()["data"]
    return {"external_id": data["id"], "name": data.get("name", data["id"]), "metadata": {"username": data.get("username", "")}}
