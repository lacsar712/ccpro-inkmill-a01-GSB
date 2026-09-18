from decimal import Decimal
from math import isfinite

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.ink_recipe_batch import (
    BATCH_STATUS_LABELS,
    BATCH_STATUSES,
    BATCH_TRANSITIONS,
    InkRecipeBatch,
)
from app.models.workshop import Workshop
from app.serializers import ink_recipe_batch_json
from app.utils import error

bp = Blueprint("ink_recipe_batches", __name__, url_prefix="/api/ink-recipe-batches")


def _validate_fields(body: dict) -> str | None:
    workshop_id = int(body.get("workshopId") or 0)
    if workshop_id <= 0:
        return "请选择所属车间"

    batch_code = str(body.get("batchCode", "")).strip()
    if not batch_code:
        return "批次编号不能为空"

    pigment_base = str(body.get("pigmentBase", "")).strip()
    if not pigment_base:
        return "色浆基料不能为空"

    try:
        target_viscosity = float(body.get("targetViscosityPaS") or 0)
    except (TypeError, ValueError):
        return "目标粘度必须是正数"
    if not isfinite(target_viscosity) or target_viscosity <= 0:
        return "目标粘度(Pa·s)必须大于 0"

    db = SessionLocal()
    try:
        if not db.get(Workshop, workshop_id):
            return "所属车间不存在"
    finally:
        db.close()

    return None


@bp.get("")
@jwt_required()
def list_batches():
    workshop_id = request.args.get("workshopId", type=int)
    status = (request.args.get("status") or "").strip()

    if status and status not in BATCH_STATUSES:
        return error("状态筛选无效，应为 draft / mixing / qc_pass / scrap", 400)

    db = SessionLocal()
    try:
        query = db.query(InkRecipeBatch)
        if workshop_id:
            query = query.filter(InkRecipeBatch.workshop_id == workshop_id)
        if status:
            query = query.filter(InkRecipeBatch.status == status)
        rows = query.order_by(InkRecipeBatch.id.desc()).all()
        return jsonify([ink_recipe_batch_json(r) for r in rows])
    finally:
        db.close()


@bp.post("")
@jwt_required()
def create_batch():
    body = request.get_json(silent=True) or {}
    err = _validate_fields(body)
    if err:
        return error(err, 400)

    db = SessionLocal()
    try:
        row = InkRecipeBatch(
            workshop_id=int(body["workshopId"]),
            batch_code=str(body["batchCode"]).strip(),
            pigment_base=str(body["pigmentBase"]).strip(),
            target_viscosity_pa_s=Decimal(str(body["targetViscosityPaS"])),
            status="draft",
            note=str(body.get("note", "")).strip() or None,
        )
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return error("该车间下批次编号已存在", 400)
        db.refresh(row)
        return jsonify(ink_recipe_batch_json(row)), 201
    finally:
        db.close()


@bp.put("/<int:item_id>")
@jwt_required()
def update_batch(item_id: int):
    body = request.get_json(silent=True) or {}
    err = _validate_fields(body)
    if err:
        return error(err, 400)

    db = SessionLocal()
    try:
        row = db.get(InkRecipeBatch, item_id)
        if not row:
            return error("配方批次不存在", 404)
        if row.status in ("qc_pass", "scrap"):
            return error(
                f"批次已是终态「{BATCH_STATUS_LABELS[row.status]}」，不可修改", 409
            )

        row.workshop_id = int(body["workshopId"])
        row.batch_code = str(body["batchCode"]).strip()
        row.pigment_base = str(body["pigmentBase"]).strip()
        row.target_viscosity_pa_s = Decimal(str(body["targetViscosityPaS"]))
        row.note = str(body.get("note", "")).strip() or None
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return error("该车间下批次编号已存在", 400)
        db.refresh(row)
        return jsonify(ink_recipe_batch_json(row))
    finally:
        db.close()


@bp.get("/<int:item_id>")
@jwt_required()
def get_batch(item_id: int):
    db = SessionLocal()
    try:
        row = db.get(InkRecipeBatch, item_id)
        if not row:
            return error("配方批次不存在", 404)
        return jsonify(ink_recipe_batch_json(row))
    finally:
        db.close()


@bp.delete("/<int:item_id>")
@jwt_required()
def delete_batch(item_id: int):
    db = SessionLocal()
    try:
        row = db.get(InkRecipeBatch, item_id)
        if not row:
            return error("配方批次不存在", 404)
        if row.status in ("qc_pass", "scrap"):
            return error(
                f"批次已是终态「{BATCH_STATUS_LABELS[row.status]}」，不可删除", 409
            )
        db.delete(row)
        db.commit()
        return jsonify({"ok": True})
    finally:
        db.close()


@bp.post("/<int:item_id>/transition")
@jwt_required()
def transition_batch(item_id: int):
    body = request.get_json(silent=True) or {}
    target = str(body.get("to") or body.get("status") or "").strip()
    if target not in BATCH_STATUSES:
        return error("目标状态无效，应为 draft / mixing / qc_pass / scrap", 400)

    db = SessionLocal()
    try:
        row = db.get(InkRecipeBatch, item_id)
        if not row:
            return error("配方批次不存在", 404)

        current = row.status
        if target == current:
            return error(
                f"批次已处于「{BATCH_STATUS_LABELS[current]}」状态，无需重复流转", 409
            )
        if target not in BATCH_TRANSITIONS.get(current, ()):
            if current in ("qc_pass", "scrap"):
                return error(
                    f"批次已是终态「{BATCH_STATUS_LABELS[current]}」，不可再流转", 409
                )
            return error(
                f"批次当前为「{BATCH_STATUS_LABELS[current]}」状态，"
                f"不能直接流转到「{BATCH_STATUS_LABELS[target]}」",
                409,
            )

        row.status = target
        db.commit()
        db.refresh(row)
        return jsonify(ink_recipe_batch_json(row))
    finally:
        db.close()
