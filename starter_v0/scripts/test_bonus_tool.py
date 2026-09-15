"""Smoke test script for bonus tool: check_hardware_warranty."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import TOOL_FUNCTIONS


def test_bonus_tool() -> None:
    print("=== Testing Bonus Tool: check_hardware_warranty ===")
    assert "check_hardware_warranty" in TOOL_FUNCTIONS, "Tool not registered in TOOL_FUNCTIONS!"
    tool = TOOL_FUNCTIONS["check_hardware_warranty"]

    # 1. Test existing asset (under warranty)
    res_valid = tool(asset_id="LT-204")
    print("\n[Case 1: Valid Asset LT-204]")
    print(res_valid)
    assert res_valid.get("tool") == "check_hardware_warranty"
    assert res_valid.get("is_under_warranty") is True
    assert res_valid.get("warranty_status") == "active"
    assert res_valid.get("days_remaining", 0) > 0
    print("=> PASS: Correctly retrieved warranty information.")

    # 2. Test missing asset_id
    res_empty = tool(asset_id="")
    print("\n[Case 2: Empty Asset ID]")
    print(res_empty)
    assert res_empty.get("error") == "missing_asset_id"
    print("=> PASS: Correctly caught missing input.")

    # 3. Test non-existent asset_id
    res_not_found = tool(asset_id="UNKNOWN-999")
    print("\n[Case 3: Non-existent Asset ID]")
    print(res_not_found)
    assert res_not_found.get("error") == "asset_not_found"
    print("=> PASS: Correctly handled not found error.")

    print("\n🎉 ALL SMOKE TESTS PASSED FOR check_hardware_warranty!")


if __name__ == "__main__":
    test_bonus_tool()
