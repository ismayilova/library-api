from flask import Blueprint, jsonify, request

from services import loan_service
from core import fines

bp = Blueprint("loans", __name__)


def loan_json(loan):
    return {
        "id": loan.id,
        "book_id": loan.book_id,
        "member_id": loan.member_id,
        "due_date": loan.due_date,
        "returned": loan.returned,
        "fine": fines.money(loan.fine),
        "fine_paid": loan.fine_paid,
        "renewals": loan.renewals,
        "checked_out": loan.checked_out,
    }


def loan_with_fine_json(loan):
    return {**loan_json(loan), "current_fine": fines.money(loan_service.current_fine(loan))}


@bp.route("/loans", methods=["GET"])
def list_loans():
    onlyOverdue = request.args.get("overdue") == "true"
    return jsonify([loan_with_fine_json(loan) for loan in loan_service.list_loans(onlyOverdue)])


@bp.route("/loans/<int:loan_id>", methods=["GET"])
def get_loan(loan_id):
    return jsonify(loan_with_fine_json(loan_service.get_loan(loan_id)))


@bp.route("/loans", methods=["POST"])
def create_loan():
    data = request.get_json(silent=True) or {}
    return jsonify(loan_json(loan_service.create_loan(data))), 201


@bp.route("/loans/<int:loan_id>/return", methods=["POST"])
def return_book(loan_id):
    return jsonify(loan_json(loan_service.return_book(loan_id)))


@bp.route("/loans/<int:loan_id>/renew", methods=["POST"])
def renew_loan(loan_id):
    return jsonify(loan_json(loan_service.renew_loan(loan_id)))


@bp.route("/loans/<int:loan_id>/pay-fine", methods=["POST"])
def pay_fine(loan_id):
    return jsonify(loan_json(loan_service.pay_fine(loan_id)))
