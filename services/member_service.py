from repositories import member_repository
from repositories import loan_repository
from services import loan_service
from core import fines
from core import validation
from core.errors import bad_request, not_found, conflict


def list_members():
    return member_repository.list_members()


def get_member(member_id):
    member = member_repository.get_member(member_id)
    if member is None:
        raise not_found("member not found")
    return member


def create_member(data):
    name, email = data.get("name"), data.get("email")
    memberType = data.get("type", "student")

    if not name:
        raise bad_request("name is required")
    if not validation.is_valid_email(email):
        raise bad_request("invalid email")
    if not validation.is_valid_member_type(memberType):
        raise bad_request("type must be student or staff")
    if member_repository.get_member_by_email(email) is not None:
        raise conflict("email already registered")

    return member_repository.create_member(name, email, memberType)


def delete_member(member_id):
    get_member(member_id)
    loans = loan_repository.list_loans_for_member(member_id)
    if loan_service.count_open_loans(loans) > 0:
        raise conflict("member has books on loan")
    if loan_service.total_owed(loans) > 0:
        raise conflict("member owes money")
    member_repository.delete_member(member_id)


def member_account(member_id):
    member = get_member(member_id)
    loans = loan_repository.list_loans_for_member(member_id)
    return {
        "loans": loans,
        "total_owed": fines.money(loan_service.total_owed(loans)),
        "loans_remaining": loan_service.loan_limit(member) - loan_service.count_open_loans(loans),
    }
