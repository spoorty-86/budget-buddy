import os
import requests
import logging
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from .models import Profile
from notifications.models import Notification as UserNotification

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
User = get_user_model()


def get_google_user_info(code, redirect_uri):
    """
    Exchanges OAuth authorization code for Google tokens and fetches user profile.
    """
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parent.parent / '.env', override=True)
    client_id = (os.environ.get('GOOGLE_CLIENT_ID') or '').strip()
    client_secret = (os.environ.get('GOOGLE_CLIENT_SECRET') or '').strip()

    if not client_id or not client_secret:
        raise ValueError("Google OAuth is not configured on the server (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET missing).")

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }

    token_res = requests.post(token_url, data=token_data, timeout=10)
    if token_res.status_code != 200:
        logger.error(f"Google token exchange failed: {token_res.status_code} - {token_res.text}")
        raise ValueError("Failed to authenticate with Google (Token exchange failed).")

    token_json = token_res.json()
    access_token = token_json.get('access_token')
    if not access_token:
        raise ValueError("No access token returned by Google.")

    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    userinfo_res = requests.get(userinfo_url, headers={'Authorization': f'Bearer {access_token}'}, timeout=10)
    if userinfo_res.status_code != 200:
        raise ValueError("Failed to retrieve Google user details.")

    info = userinfo_res.json()
    email = info.get('email')
    if not email:
        raise ValueError("Google account did not provide a valid email address.")

    return {
        'email': email,
        'first_name': info.get('given_name', ''),
        'last_name': info.get('family_name', ''),
        'avatar': info.get('picture', ''),
        'id': info.get('sub', ''),
        'username_hint': email.split('@')[0]
    }


def get_github_user_info(code, redirect_uri):
    """
    Exchanges OAuth authorization code for GitHub tokens and fetches user profile.
    """
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parent.parent / '.env', override=True)
    client_id = (os.environ.get('GITHUB_CLIENT_ID') or '').strip()
    client_secret = (os.environ.get('GITHUB_CLIENT_SECRET') or '').strip()

    if not client_id or not client_secret:
        raise ValueError("GitHub OAuth is not configured on the server (GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET missing).")

    token_url = "https://github.com/login/oauth/access_token"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri,
    }

    token_res = requests.post(token_url, headers=headers, json=token_data, timeout=10)
    if token_res.status_code != 200:
        logger.error(f"GitHub token exchange failed: {token_res.status_code} - {token_res.text}")
        raise ValueError("Failed to authenticate with GitHub (Token exchange failed).")

    token_json = token_res.json()
    access_token = token_json.get('access_token')
    if not access_token:
        error_desc = token_json.get('error_description', 'No access token returned by GitHub.')
        raise ValueError(f"GitHub authentication error: {error_desc}")

    user_headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': 'BudgetBuddy-App'
    }
    user_res = requests.get("https://api.github.com/user", headers=user_headers, timeout=10)
    if user_res.status_code != 200:
        raise ValueError("Failed to retrieve GitHub user details.")

    info = user_res.json()
    email = info.get('email')

    # GitHub users can have private emails, check /user/emails endpoint if missing
    if not email:
        emails_res = requests.get("https://api.github.com/user/emails", headers=user_headers, timeout=10)
        if emails_res.status_code == 200:
            emails = emails_res.json()
            primary_email = next((e['email'] for e in emails if e.get('primary') and e.get('verified')), None)
            email = primary_email or (emails[0]['email'] if emails else None)

    if not email:
        raise ValueError("GitHub account did not provide a verified public/private email address.")

    name = info.get('name') or info.get('login', '')
    name_parts = name.split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    return {
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'avatar': info.get('avatar_url', ''),
        'id': str(info.get('id', '')),
        'username_hint': info.get('login') or email.split('@')[0]
    }


def get_or_create_oauth_user(provider, email, first_name='', last_name='', avatar=None, username_hint=None):
    """
    Retrieves or creates a Django User by email from social login.
    """
    user = User.objects.filter(email__iexact=email).first()

    if user:
        # Update user names if missing
        updated = False
        if not user.first_name and first_name:
            user.first_name = first_name
            updated = True
        if not user.last_name and last_name:
            user.last_name = last_name
            updated = True
        if updated:
            user.save()

        # Update profile avatar / full name with latest OAuth provider data
        profile, _ = Profile.objects.get_or_create(user=user)
        profile_updated = False
        full_name = f"{first_name} {last_name}".strip()
        if full_name and (not profile.full_name or profile.full_name == user.username):
            profile.full_name = full_name
            profile_updated = True
        if avatar:
            profile.avatar = avatar
            profile_updated = True
        if profile_updated:
            profile.save()

        return user

    # Generate a unique username
    base_username = (username_hint or email.split('@')[0]).replace(' ', '_')
    # Sanitize base username for Django User validation
    base_username = ''.join(c for c in base_username if c.isalnum() or c in ['_', '.'])[:20]
    if not base_username:
        base_username = f"user_{provider}"

    username = base_username
    counter = 1
    while User.objects.filter(username__iexact=username).exists():
        username = f"{base_username}_{counter}"
        counter += 1

    # Create new user with unusable password
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name
    )
    user.set_unusable_password()
    user.save()

    # Update Profile
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.full_name = f"{first_name} {last_name}".strip() or username
    if avatar:
        profile.avatar = avatar
    profile.save()
    user.profile = profile

    # Send Welcome Notification
    try:
        UserNotification.objects.create(
            user=user,
            title=f"Welcome to BudgetBuddy ({provider.title()})",
            message=f"Welcome to BudgetBuddy! Your account was created using {provider.title()}. You are now signed in.",
            notification_type="SUCCESS"
        )
    except Exception as e:
        logger.warning(f"Failed to create welcome notification for OAuth user: {e}")

    return user
