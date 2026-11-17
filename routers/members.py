from flask import Blueprint, request, jsonify
from services import members

members_router = Blueprint("members", __name__)

@members_router.get("/members")
def list_members():
    return jsonify(members.list_members())

@members_router.get("/members/<int:member_id>")
def get_member(member_id):
    return jsonify(members.get_member(member_id))

@members_router.post("/members")
def create_member():
    return jsonify(members.create_member(request.get_json(silent=True) or {})), 201

@members_router.get("/members/<int:member_id>/loans")
def member_loans(member_id):
    return jsonify(members.member_loans(member_id))
