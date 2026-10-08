import pytest

import app as app_module
from app import create_app
from splitter import split_evenly


@pytest.fixture
def client():
    # The store is module-level, so reset it between tests rather than letting
    # one test's expenses leak into the next one's balances.
    app_module._expenses.clear()
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_health_reports_the_configured_currency(client):
    body = client.get("/health").get_json()
    assert body["status"] == "ok"
    assert body["currency"]


def test_split_three_ways():
    assert split_evenly(900, ["ana", "ben", "cal"]) == {
        "ana": 300,
        "ben": 300,
        "cal": 300,
    }


VALID = {"amount_cents": 900, "paid_by": "ana", "participants": ["ana", "ben"]}


@pytest.mark.parametrize("field", ["amount_cents", "paid_by", "participants"])
def test_missing_field_is_a_400_not_a_500(client, field):
    payload = {k: v for k, v in VALID.items() if k != field}
    resp = client.post("/expenses", json=payload)
    assert resp.status_code == 400
    assert any(field in d for d in resp.get_json()["details"])


@pytest.mark.parametrize(
    "overrides",
    [
        {"amount_cents": 9.5},
        {"amount_cents": "900"},
        {"amount_cents": True},
        {"amount_cents": 0},
        {"amount_cents": -100},
        {"paid_by": ""},
        {"paid_by": 7},
        {"participants": []},
        {"participants": "ben"},
        {"participants": ["ana", ""]},
        {"participants": ["ana", "ana"]},
    ],
)
def test_invalid_values_are_rejected(client, overrides):
    resp = client.post("/expenses", json={**VALID, **overrides})
    assert resp.status_code == 400


@pytest.mark.parametrize("raw", [b"not json", b"[]", b"null"])
def test_non_object_body_is_rejected(client, raw):
    resp = client.post("/expenses", data=raw, content_type="application/json")
    assert resp.status_code == 400


def test_rejected_expense_is_not_stored(client):
    client.post("/expenses", json={"amount_cents": 900})
    assert app_module._expenses == []


def test_valid_expense_is_accepted(client):
    assert client.post("/expenses", json=VALID).status_code == 201

def test_split_distributes_the_remainder_in_list_order():
    assert split_evenly(100, ["ana", "ben", "cal"]) == {
        "ana": 34,
        "ben": 33,
        "cal": 33,
    }

@pytest.mark.parametrize("amount", [0, 1, 2, 99, 100, 101, 1000, 1001])
@pytest.mark.parametrize("n", [1, 2, 3, 4, 7])
def test_split_shares_always_sum_to_the_amount(amount, n):
    people = [f"p{i}" for i in range(n)]
    shares = split_evenly(amount, people)
    assert sum(shares.values()) == amount
    assert max(shares.values()) - min(shares.values()) <= 1


def test_balances_sum_to_zero_when_amounts_do_not_divide_evenly(client):
    for amount, payer in [(100, "ana"), (101, "ben"), (1, "cal"), (1000, "ana")]:
        client.post(
            "/expenses",
            json={
                "amount_cents": amount,
                "paid_by": payer,
                "participants": ["ana", "ben", "cal"],
            },
        )
    body = client.get("/balances").get_json()
    assert sum(body["balances"].values()) == 0

def test_payer_is_credited_the_others_shares(client):
    client.post(
        "/expenses",
        json={
            "amount_cents": 900,
            "paid_by": "ana",
            "participants": ["ana", "ben", "cal"],
        },
    )
    body = client.get("/balances").get_json()
    assert body["balances"]["ana"] == 600
    assert body["balances"]["ben"] == -300
