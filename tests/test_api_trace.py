import json
import unittest
from unittest.mock import Mock
import requests
from travel.api_trace import TRACE, exchange


class TraceTests(unittest.TestCase):
    def test_records_request_response_and_redacts_keys(self):
        trace = []
        token = TRACE.set(trace)
        try:
            response = Mock(status_code=200)
            response.json.return_value = {'documents': [], 'echo': 'secret-key'}
            exchange(Mock(return_value=response), 'https://example.com', provider='kakao',
                     stage='restaurant_search', secrets=('secret-key',),
                     params={'query': '강릉 맛집'}, headers={'Authorization': 'secret-key'})
            self.assertEqual(trace[0]['request']['params']['query'], '강릉 맛집')
            self.assertEqual(trace[0]['response']['status_code'], 200)
            self.assertNotIn('secret-key', json.dumps(trace))
            self.assertNotIn('headers', trace[0]['request'])
        finally:
            TRACE.reset(token)

    def test_timeout_remains_recorded_without_exception_secrets(self):
        trace = []
        token = TRACE.set(trace)
        try:
            with self.assertRaises(requests.Timeout):
                exchange(Mock(side_effect=requests.Timeout('secret-key')), 'https://example.com',
                         provider='gemini', stage='report', secrets=('secret-key',), json={})
            self.assertEqual(trace[0]['error']['type'], 'Timeout')
            self.assertNotIn('secret-key', json.dumps(trace))
        finally:
            TRACE.reset(token)
