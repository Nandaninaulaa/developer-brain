"""
WSGI config for devbrain_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devbrain_project.settings')

application = get_wsgi_application()

# Preload the embedding model once at server boot (only when actually
# serving via gunicorn — guarded by PRELOAD_EMBEDDING_MODEL, which
# entrypoint.sh sets only for the gunicorn step, not for migrate/
# collectstatic). Without this, the first real ingest/ask request pays
# the full cost of downloading + loading the model, which was slow
# enough on constrained free-tier CPU to blow past the platform's
# request timeout and return a 502 before the app ever got a chance to
# respond. Loading it here instead happens during boot, which Render
# tolerates for much longer than a single HTTP request.
if os.getenv('PRELOAD_EMBEDDING_MODEL') == 'true':
    try:
        from brain_app import config as brain_config
        if brain_config.EMBEDDING_PROVIDER == 'local':
            print('==> Preloading local embedding model...', file=sys.stderr, flush=True)
            from brain_app.embeddings import get_embedding_provider
            get_embedding_provider()
            print('==> Embedding model preloaded.', file=sys.stderr, flush=True)
    except Exception as e:
        # Never let a preload failure block the server from starting —
        # worst case it just falls back to loading lazily on first use.
        print(f'==> Embedding model preload skipped: {e}', file=sys.stderr, flush=True)
