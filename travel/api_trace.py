"""Capture API exchanges without authentication headers."""
from contextvars import ContextVar
from datetime import datetime, timezone
from time import monotonic
import requests

TRACE = ContextVar('api_trace', default=None)


def exchange(send, url, *, provider, stage, secrets=(), **kwargs):
    trace = TRACE.get()
    if trace is None:
        return send(url, **kwargs)

    def sanitize(value):
        if isinstance(value, str):
            for secret in secrets:
                if secret:
                    value = value.replace(secret, '[REDACTED]')
            return value
        if isinstance(value, dict):
            return {key: sanitize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [sanitize(item) for item in value]
        return value

    entry = {'sequence': len(trace) + 1, 'provider': provider, 'stage': stage,
             'requested_at': datetime.now(timezone.utc).isoformat(),
             'request': {'method': 'POST' if 'json' in kwargs else 'GET', 'url': url}}
    for name in ('params', 'json'):
        if name in kwargs:
            entry['request'][name] = sanitize(kwargs[name])
    trace.append(entry)
    started = monotonic()
    try:
        response = send(url, **kwargs)
        try:
            body = response.json()
        except ValueError:
            body = response.text
        entry['response'] = {'status_code': response.status_code, 'body': sanitize(body)}
        return response
    except requests.RequestException as exc:
        entry['error'] = {'type': type(exc).__name__}
        raise
    finally:
        entry['duration_ms'] = round((monotonic() - started) * 1000, 2)
