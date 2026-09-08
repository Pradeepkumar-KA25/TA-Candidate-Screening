from __future__ import annotations

import httpx
import pytest

from app.integrations.zoho_recruit import (
    ZohoRecruitClient,
    ZohoRecruitPermanentError,
    ZohoRecruitTransientError,
)


class FakeHttpClient:
    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = responses
        self.calls = 0

    def get(self, endpoint: str, headers=None, params=None):
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return response


def test_fetch_candidates_page_success() -> None:
    fake_client = FakeHttpClient(
        [
            httpx.Response(
                status_code=200,
                json={
                    'data': [{'id': 'z-1'}, {'id': 'z-2'}],
                    'info': {'more_records': False},
                },
            )
        ]
    )
    client = ZohoRecruitClient(client=fake_client)

    page = client.fetch_candidates_page(access_token='token', page=1, per_page=200)

    assert len(page.candidates) == 2
    assert page.has_more is False


def test_iter_candidates_handles_pagination() -> None:
    fake_client = FakeHttpClient(
        [
            httpx.Response(status_code=200, json={'data': [{'id': 'z-1'}], 'info': {'more_records': True}}),
            httpx.Response(status_code=200, json={'data': [{'id': 'z-2'}], 'info': {'more_records': False}}),
        ]
    )
    client = ZohoRecruitClient(client=fake_client)

    rows = list(client.iter_candidates(access_token='token', per_page=1))

    assert [row['id'] for row in rows] == ['z-1', 'z-2']
    assert fake_client.calls == 2


def test_fetch_candidates_retries_transient_failures(monkeypatch) -> None:
    monkeypatch.setattr('app.integrations.zoho_recruit.time.sleep', lambda _: None)
    fake_client = FakeHttpClient(
        [
            httpx.Response(status_code=503, json={'message': 'upstream down'}),
            httpx.Response(status_code=200, json={'data': [{'id': 'z-1'}], 'info': {'more_records': False}}),
        ]
    )
    client = ZohoRecruitClient(client=fake_client)

    page = client._fetch_candidates_page_with_retry(access_token='token', page=1, per_page=200)

    assert len(page.candidates) == 1
    assert fake_client.calls == 2


def test_fetch_candidates_raises_permanent_error_for_bad_response_shape() -> None:
    fake_client = FakeHttpClient([httpx.Response(status_code=200, json={'items': []})])
    client = ZohoRecruitClient(client=fake_client)

    with pytest.raises(ZohoRecruitPermanentError):
        client.fetch_candidates_page(access_token='token', page=1, per_page=200)


def test_fetch_candidates_raises_after_retries(monkeypatch) -> None:
    monkeypatch.setattr('app.integrations.zoho_recruit.time.sleep', lambda _: None)
    fake_client = FakeHttpClient([httpx.Response(status_code=503, json={'message': 'retry'})])
    client = ZohoRecruitClient(client=fake_client)

    with pytest.raises(ZohoRecruitTransientError):
        client._fetch_candidates_page_with_retry(access_token='token', page=1, per_page=200)
