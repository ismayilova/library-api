from flask import Blueprint, request, jsonify
from services import loans

loans_router = Blueprint("loans", __name__)

@loans_router.get("/loans")
def list_loans():
    return jsonify(loans.list_loans(request.args.get("overdue") == "true"))

@loans_router.get("/loans/<int:loan_id>")
def get_loan(loan_id):
    return jsonify(loans.get_loan(loan_id))

@loans_router.post("/loans")
def create_loan():
    return jsonify(loans.create_loan(request.get_json(silent=True) or {})), 201

@loans_router.post("/loans/<int:loan_id>/return")
def return_book(loan_id):
    return jsonify(loans.return_book(loan_id))

@loans_router.post("/loans/<int:loan_id>/renew")
def renew_loan(loan_id):
    return jsonify(loans.renew_loan(loan_id))

@loans_router.post("/loans/<int:loan_id>/pay-fine")
def pay_fine(loan_id):
    return jsonify(loans.pay_fine(loan_id))

@loans_router.get("/reports/overdue")
def overdue_report():
    return jsonify(loans.overdue_report())

@loans_router.get("/reports/summary")
def summary_report():
    return jsonify(loans.summary_report())
