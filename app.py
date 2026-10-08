"""A small expense-sharing API. Flask, in-memory, no database. """

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from splitter import balances

load_dotenv()
CURRENCY = os.environ["LEDGER_CURRENCY"]

_expenses = []


def _is_name(value):
    return isinstance(value, str) and value.strip() != ""


def _validate_expense(body):
    """Return a list of human-readable problems; empty means the body is valid."""
    if not isinstance(body, dict):
        return ["request body must be a JSON object"]

    errors = []

    amount = body.get("amount_cents")
    if "amount_cents" not in body:
        errors.append("amount_cents is required")
    # bool is an int subclass; reject it explicitly. Floats are never money.
    elif isinstance(amount, bool) or not isinstance(amount, int):
        errors.append("amount_cents must be an integer number of cents")
    elif amount <= 0:
        errors.append("amount_cents must be greater than zero")

    if "paid_by" not in body:
        errors.append("paid_by is required")
    elif not _is_name(body["paid_by"]):
        errors.append("paid_by must be a non-empty string")

    if "participants" not in body:
        errors.append("participants is required")
    else:
        participants = body["participants"]
        if not isinstance(participants, list) or not participants:
            errors.append("participants must be a non-empty list")
        elif not all(_is_name(p) for p in participants):
            errors.append("participants must contain only non-empty strings")
        elif len(set(participants)) != len(participants):
            # Shares are keyed by person, so a duplicate would silently drop
            # money and break the zero-sum invariant.
            errors.append("participants must not contain duplicates")

    return errors

def create_app():
    
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify(status="ok", currency=CURRENCY)

    @app.post("/expenses")
    def add_expense():
        body = request.get_json(silent=True)
        errors = _validate_expense(body)
        if errors:
            return jsonify(error="invalid expense", details=errors), 400
        _expenses.append(
            {
                "amount_cents": body["amount_cents"],
                "paid_by": body["paid_by"],
                "participants": body["participants"],
            }
        )
        return jsonify(ok=True), 201

    @app.get("/balances")
    def get_balances():
        people = sorted(
            {p for e in _expenses for p in e["participants"]}
            | {e["paid_by"] for e in _expenses}
        )
        return jsonify(currency=CURRENCY, balances=balances(_expenses, people))

    return app


if __name__ == "__main__":
    create_app().run(port=int(os.environ.get("PORT", "5000")))
