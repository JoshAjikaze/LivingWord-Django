# Social publishing setup

The admin social publishing hub supports **Facebook Pages, Instagram Professional accounts, Threads, YouTube, and X/Twitter** through direct provider APIs. An administrator can connect accounts from **Admin → Social publishing → Social accounts**, create a post under **Social posts**, select one or more connected accounts, attach image or video assets, and use the **Queue selected posts for publishing** action.

## Required environment values

Copy `.env.example` to `.env` and set the following values. The OAuth redirect base must be the public HTTPS origin of the deployed application.

```dotenv
SOCIAL_TOKEN_ENCRYPTION_KEY=<Fernet key>
SOCIAL_OAUTH_REDIRECT_BASE=https://library.example.com
SOCIAL_FACEBOOK_CLIENT_ID=
SOCIAL_FACEBOOK_CLIENT_SECRET=
SOCIAL_INSTAGRAM_CLIENT_ID=
SOCIAL_INSTAGRAM_CLIENT_SECRET=
SOCIAL_THREADS_CLIENT_ID=
SOCIAL_THREADS_CLIENT_SECRET=
SOCIAL_YOUTUBE_CLIENT_ID=
SOCIAL_YOUTUBE_CLIENT_SECRET=
SOCIAL_X_CLIENT_ID=
SOCIAL_X_CLIENT_SECRET=
```

Generate the encryption key with:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Never rotate this key without first migrating or re-encrypting existing social tokens. The application encrypts access and refresh tokens before storing them in the database.

## Provider setup

Create an application in each provider’s developer console and register the exact callback URL shown below:

```text
https://library.example.com/social/oauth/facebook/callback/
https://library.example.com/social/oauth/instagram/callback/
https://library.example.com/social/oauth/threads/callback/
https://library.example.com/social/oauth/youtube/callback/
https://library.example.com/social/oauth/x/callback/
```

Meta publishing requires an approved Meta application, a Facebook Page access token and the relevant Page permissions. Instagram publishing requires an Instagram Professional account connected to a Facebook Page and public HTTPS media URLs. Threads requires Threads API permissions. YouTube requires OAuth consent configuration and YouTube Data API access. X requires a developer project with user-context posting and media-upload access; the available operations depend on the account’s X API plan.

## Queue worker

The admin action creates one delivery record per selected account. Publishing is deliberately asynchronous so video uploads do not block an admin request. Run the worker continuously or from a scheduler:

```bash
python3 manage.py process_social_queue --limit 20
```

A cron example that runs every minute is:

```cron
* * * * * cd /srv/livingword && /srv/venv/bin/python manage.py process_social_queue --limit 20 >> /var/log/livingword-social.log 2>&1
```

Each delivery is independently tracked as `QUEUED`, `PUBLISHING`, `SUCCESS`, or `FAILED`. Failed deliveries record the provider response and receive exponential retry delays. The admin action **Retry selected failed deliveries now** resets a failed delivery to the queue.

## Platform behavior

The composer accepts a base caption, optional link, and reusable media assets. Before queueing, the application validates the post against each selected platform. YouTube requires exactly one video and a title. Instagram requires media. X limits text to 280 characters and four media attachments. Threads limits text to 500 characters. Media must be publicly retrievable over HTTPS because Meta and Threads fetch media from the supplied URL; local development media URLs are rejected by the publisher until the site is exposed through HTTPS.

The initial implementation intentionally defaults YouTube uploads to **private**. Change the connected account metadata value `default_privacy` to `unlisted` or `public` only after the channel and moderation workflow have been tested.

## Verification checklist

Run:

```bash
python3 manage.py migrate
python3 manage.py check
python3 manage.py makemigrations --check --dry-run
python3 -m pytest -q
```

For a safe staging test, connect accounts with test credentials, upload a small test image and short video, create a post with one destination at a time, queue it, run the worker once, and verify both the provider post and the corresponding `SocialDelivery` response payload. Do not use production audience visibility until each provider’s test flow is approved.

## Official references

[Facebook Pages API](https://developers.facebook.com/documentation/pages-api)

[Instagram Content Publishing](https://developers.facebook.com/documentation/instagram-platform/content-publishing)

[Threads API](https://developers.facebook.com/documentation/threads/overview)

[YouTube video upload](https://developers.google.com/youtube/v3/guides/uploading_a_video)

[X API media upload](https://docs.x.com/x-api/media/introduction)
