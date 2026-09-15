from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from tools._shared import ROOT, err

ASSET_FILE = ROOT / "helpdesk_data" / "assets.json"


def check_hardware_warranty(asset_id: str = "") -> dict[str, Any]:
    """Check hardware warranty status and expiration for a company asset."""
    try:
        data = json.loads(ASSET_FILE.read_text(encoding="utf-8"))
        wanted_id = (asset_id or "").strip().upper()
        if not wanted_id:
            return {
                "tool": "check_hardware_warranty",
                "error": "missing_asset_id",
                "message": "Asset ID is required to check warranty.",
            }

        device = next((item for item in data.get("assets", []) if item.get("asset_id") == wanted_id), None)
        if device is None:
            return {
                "tool": "check_hardware_warranty",
                "asset_id": wanted_id,
                "error": "asset_not_found",
                "message": f"Asset {wanted_id} not found in hardware inventory.",
            }

        purchase_date_str = device.get("purchase_date")
        warranty_until_str = device.get("warranty_until")

        # Snapshot reference date from dataset (default 2026-09-14)
        snapshot_str = data.get("snapshot_at", "2026-09-14T09:00:00+07:00")
        try:
            ref_date = datetime.fromisoformat(snapshot_str).date()
        except Exception:
            ref_date = datetime.now().date()

        is_under_warranty = False
        days_remaining = None
        warranty_status = "unknown"

        if warranty_until_str:
            try:
                warranty_date = datetime.strptime(warranty_until_str, "%Y-%m-%d").date()
                days_remaining = (warranty_date - ref_date).days
                if days_remaining > 0:
                    is_under_warranty = True
                    warranty_status = "active" if days_remaining > 90 else "expiring_soon"
                else:
                    is_under_warranty = False
                    warranty_status = "expired"
            except Exception:
                warranty_status = "unparseable_date"

        return {
            "tool": "check_hardware_warranty",
            "asset_id": wanted_id,
            "manufacturer": device.get("manufacturer"),
            "model": device.get("model"),
            "assigned_to": device.get("assigned_to"),
            "purchase_date": purchase_date_str,
            "warranty_until": warranty_until_str,
            "is_under_warranty": is_under_warranty,
            "warranty_status": warranty_status,
            "days_remaining": days_remaining,
            "reference_date": str(ref_date),
        }
    except Exception as exc:
        return err("check_hardware_warranty", exc)
