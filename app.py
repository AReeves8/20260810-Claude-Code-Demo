"""A small expense-sharing API. Flask, in-memory, no database. """

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from splitter import balances

load_dotenv()
CURRENCY = os.environ["LEDGER_CURRENCY"]

_expenses = []

def create_app():
    
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify(status="ok", currency=CURRENCY)

    @app.post("/expenses")
    def add_expense():
        body = request.get_json(silent=True) or {}
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
