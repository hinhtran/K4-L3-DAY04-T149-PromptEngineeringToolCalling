"""Script to generate standard required transcripts for Track B using live Gemini API.
Scenarios:
1. Normal query (inspect device diagnostics)
2. Missing information (clarification flow)
3. Multi-turn correction (carry context & update employee)
4. Write action with confirmation boundary (create ticket)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chat import run_model_tool_loop, write_transcript, trim_history
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

load_lab_env(ROOT)

SCENARIOS = [
    {
        "id": "scenario_normal_query",
        "description": "Yêu cầu bình thường: Kiểm tra chẩn đoán thiết bị LT-204",
        "conversations": [
            "Kiểm tra tình trạng thiết bị laptop LT-204 giúp mình."
        ]
    },
    {
        "id": "scenario_missing_info",
        "description": "Thiếu thông tin: Báo sự cố nhưng thiếu Asset ID, sau đó bổ sung",
        "conversations": [
            "Laptop của mình bị lỗi không thể truy cập được Wi-Fi văn phòng, hãy kiểm tra máy giúp mình.",
            "Mã máy của mình là LT-240, chỉ kiểm tra phần network thôi nhé."
        ]
    },
    {
        "id": "scenario_multiturn_correction",
        "description": "Nhiều lượt sửa đổi: Tra cứu nhân viên EMP-1001 rồi đính chính thành EMP-1005",
        "conversations": [
            "Tra cứu thông tin tài khoản và thiết bị cấp phát của nhân viên EMP-1001.",
            "À mình gõ nhầm mã, mã chính xác của nhân sự phòng Pháp chế là EMP-1005, tra cứu lại nhé."
        ]
    },
    {
        "id": "scenario_write_confirmation",
        "description": "Hành động ghi cần xác nhận: Tạo ticket hỗ trợ kỹ thuật",
        "conversations": [
            "Hãy tạo một ticket hỗ trợ kỹ thuật: Màn hình máy tính DT-031 bị chớp tắt liên tục, mức ưu tiên high.",
            "Tôi đã xem lại và xác nhận toàn bộ thông tin trên, hãy tạo ticket chính thức."
        ]
    }
]


def run_scenario(scenario: dict, provider_name: str = "gemini", version: str = "v0") -> Path:
    system_prompt_path = ROOT / "artifacts" / "system_prompt.md"
    tools_path = ROOT / "artifacts" / "tools.yaml"
    transcripts_dir = ROOT / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    tool_decls = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_decls)
    provider = make_provider(provider_name)
    artifact_version = build_artifact_version(version, system_prompt_path, tools_path)

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    transcript_id = f"{version}_{provider_name}_{scenario['id']}_{timestamp}"
    out_path = transcripts_dir / f"{transcript_id}.transcript.json"

    transcript = {
        "transcript_id": transcript_id,
        "scenario_id": scenario["id"],
        "scenario_description": scenario["description"],
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": getattr(provider, "default_model", "gemini-3.5-flash"),
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": 5,
        "max_tool_rounds": 4,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "turns": [],
    }

    history: list[dict[str, str]] = []
    print(f"\n========================================================")
    print(f"🎬 Running Scenario: {scenario['id']}")
    print(f"📌 {scenario['description']}")
    print(f"========================================================")

    for turn_index, user_text in enumerate(scenario["conversations"], 1):
        print(f"\n👤 You [{version}]> {user_text}")
        messages = [
            {"role": "system", "content": system_prompt},
            *trim_history(history, 5),
            {"role": "user", "content": user_text},
        ]
        turn_record = {
            "turn_index": turn_index,
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "user": user_text,
            "status": "started",
            "assistant_text": None,
            "rounds": [],
            "tool_events": [],
        }

        try:
            result = run_model_tool_loop(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=None,
                max_tool_rounds=4,
                version=version,
            )
            turn_record.update(result)
            assistant_text = result.get("assistant_text", "")
            print(f"\n💬 Agent [{version}]> {assistant_text}")
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": assistant_text})
        except Exception as exc:
            turn_record.update({
                "status": "provider_error",
                "error": f"{type(exc).__name__}: {str(exc)}",
            })
            print(f"\n❌ ERROR> {turn_record['error']}")

        turn_record["ended_at"] = datetime.now().isoformat(timespec="seconds")
        transcript["turns"].append(turn_record)
        write_transcript(out_path, transcript)
        import time
        time.sleep(2)

    print(f"💾 Transcript saved to: {out_path}")
    return out_path


def main():
    print("🚀 Starting automated recording of required transcripts for Track B...")
    saved_files = []
    for sc in SCENARIOS:
        p = run_scenario(sc, provider_name="openrouter", version="v0")
        saved_files.append(p)
    print("\n🎉 ALL 4 REQUIRED TRANSCRIPTS SUCCESSFULLY GENERATED!")
    for f in saved_files:
        print(f" - {f.name}")


if __name__ == "__main__":
    main()
