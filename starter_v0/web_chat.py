"""Light-themed Web Demo UI for IT Helpdesk Agent.
Supports switching between versions (v0, v1, v2, v3) and providers (openrouter, gemini).
Displays real-time Tool Calls, Input Payloads, Results, and Errors.
Automatically saves transcripts to starter_v0/transcripts/.
"""
from __future__ import annotations

import json
import os
import sys
import webbrowser
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from chat import run_model_tool_loop, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

load_lab_env(ROOT)

PORT = 8000
SYSTEM_PROMPT_PATH = ROOT / "artifacts" / "system_prompt.md"
TOOLS_PATH = ROOT / "artifacts" / "tools.yaml"
TRANSCRIPTS_DIR = ROOT / "transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

HTML_CONTENT = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IT Helpdesk Agent — Demo Interface</title>
  <style>
    :root {
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --primary-light: #eff6ff;
      --tool-bg: #fffbeb;
      --tool-border: #f59e0b;
      --tool-header: #b45309;
      --success: #16a34a;
      --error: #dc2626;
      --code-bg: #f1f5f9;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    body { background: var(--bg); color: var(--text); display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

    /* Top Navbar */
    header {
      background: var(--card-bg);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
      flex-shrink: 0;
    }
    .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.15rem; color: #1e293b; }
    .brand span.badge {
      background: #dbeafe; color: #1e40af; font-size: 0.75rem; padding: 3px 8px; border-radius: 999px; font-weight: 600;
    }

    /* Version & Provider Selector */
    .controls { display: flex; align-items: center; gap: 16px; }
    .selector-group { display: flex; align-items: center; gap: 6px; font-size: 0.88rem; color: var(--text-muted); }
    .version-pills { display: flex; background: #e2e8f0; padding: 3px; border-radius: 8px; }
    .version-btn {
      border: none; background: transparent; padding: 5px 12px; font-size: 0.82rem; font-weight: 600;
      color: #475569; border-radius: 6px; cursor: pointer; transition: all 0.15s;
    }
    .version-btn.active { background: var(--card-bg); color: var(--primary); box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .select-input {
      padding: 6px 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--card-bg);
      font-size: 0.85rem; font-weight: 500; color: var(--text); outline: none;
    }

    /* Main Chat Container */
    main {
      flex: 1; max-width: 960px; width: 100%; margin: 0 auto; display: flex; flex-direction: column;
      background: var(--card-bg); border-left: 1px solid var(--border); border-right: 1px solid var(--border);
      overflow: hidden;
    }

    .chat-history { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 20px; }

    /* Messages */
    .message { display: flex; flex-direction: column; gap: 6px; max-width: 85%; }
    .message.user { align-self: flex-end; align-items: flex-end; }
    .message.assistant { align-self: flex-start; }

    .sender-label { font-size: 0.75rem; font-weight: 600; color: var(--text-muted); }
    .bubble {
      padding: 12px 16px; border-radius: 12px; font-size: 0.95rem; line-height: 1.55; white-space: pre-wrap; word-break: break-word;
    }
    .message.user .bubble { background: var(--primary); color: white; border-bottom-right-radius: 3px; }
    .message.assistant .bubble { background: #f8fafc; border: 1px solid var(--border); color: #1e293b; border-bottom-left-radius: 3px; }

    /* Tool Call Card */
    .tool-card {
      align-self: flex-start; width: 100%; max-width: 780px; background: var(--tool-bg);
      border: 1px solid var(--tool-border); border-left: 4px solid var(--tool-border);
      border-radius: 8px; padding: 12px 16px; font-size: 0.85rem; box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .tool-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; font-weight: 700; color: var(--tool-header); }
    .tool-name { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; background: #fef3c7; padding: 2px 6px; border-radius: 4px; }
    .tool-body { display: flex; flex-direction: column; gap: 8px; }
    .tool-section-title { font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.5px; }
    .tool-section-title.input { color: #b45309; }
    .tool-section-title.result { color: var(--success); }
    .tool-section-title.error { color: var(--error); }
    pre.code-block {
      background: var(--card-bg); border: 1px solid #fde68a; border-radius: 6px; padding: 8px 10px;
      font-size: 0.8rem; overflow-x: auto; font-family: ui-monospace, SFMono-Regular, monospace; color: #1e293b;
    }

    /* Suggestion Chips */
    .chips-bar {
      padding: 10px 24px; background: var(--card-bg); border-top: 1px solid #f1f5f9;
      display: flex; gap: 8px; overflow-x: auto; flex-shrink: 0;
    }
    .chip {
      background: var(--primary-light); color: var(--primary); border: 1px solid #bfdbfe;
      padding: 5px 12px; border-radius: 999px; font-size: 0.8rem; font-weight: 500;
      white-space: nowrap; cursor: pointer; transition: all 0.15s;
    }
    .chip:hover { background: #dbeafe; }

    /* Input Footer */
    footer {
      padding: 16px 24px; background: var(--card-bg); border-top: 1px solid var(--border);
      display: flex; gap: 12px; align-items: center; flex-shrink: 0;
    }
    .input-box {
      flex: 1; padding: 12px 16px; border-radius: 10px; border: 1px solid var(--border);
      background: #f8fafc; font-size: 0.95rem; outline: none; transition: border 0.15s;
    }
    .input-box:focus { border-color: var(--primary); background: white; }
    .send-btn {
      background: var(--primary); color: white; border: none; padding: 12px 22px;
      border-radius: 10px; font-weight: 600; font-size: 0.95rem; cursor: pointer; transition: background 0.15s;
    }
    .send-btn:hover { background: var(--primary-hover); }
    .send-btn:disabled { background: #94a3b8; cursor: not-allowed; }

    .loading-indicator { font-size: 0.85rem; color: var(--text-muted); font-style: italic; display: flex; align-items: center; gap: 6px; }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      🤖 IT Helpdesk Agent <span class="badge">Live Demo</span>
    </div>
    <div class="controls">
      <div class="selector-group">
        <span>Phiên bản:</span>
        <div class="version-pills">
          <button class="version-btn active" onclick="setVersion('v0')">v0 (Baseline)</button>
          <button class="version-btn" onclick="setVersion('v1')">v1 (Prompt)</button>
          <button class="version-btn" onclick="setVersion('v2')">v2 (Tools)</button>
          <button class="version-btn" onclick="setVersion('v3')">v3 (Safe)</button>
        </div>
      </div>
      <div class="selector-group">
        <span>Provider:</span>
        <select id="provider-select" class="select-input" onchange="switchProvider()">
          <option value="openrouter" selected>OpenRouter (GPT-4o-mini)</option>
          <option value="gemini">Google Gemini (3.6-flash)</option>
        </select>
      </div>
    </div>
  </header>

  <main>
    <div id="chat-history" class="chat-history">
      <div class="message assistant">
        <div class="sender-label">Agent (v0)</div>
        <div class="bubble">Xin chào! Tôi là Trợ lý IT Helpdesk. Bạn có thể hỏi tôi về trạng thái dịch vụ (VPN, SSO, Wi-Fi), chẩn đoán thiết bị, tra cứu nhân viên, thông tin bảo hành (Bonus), hoặc tạo ticket hỗ trợ.</div>
      </div>
    </div>

    <div class="chips-bar">
      <div class="chip" onclick="quickAsk('Kiểm tra tình trạng bảo hành của laptop LT-204 giúp mình.')">🔍 Bảo hành LT-204 (Bonus)</div>
      <div class="chip" onclick="quickAsk('Kiểm tra kết nối mạng trên máy LT-240.')">💻 Chẩn đoán LT-240</div>
      <div class="chip" onclick="quickAsk('Dịch vụ VPN trên production hiện có ổn định không?')">🌐 VPN Production</div>
      <div class="chip" onclick="quickAsk('Tra cứu thông tin tài khoản của nhân viên EMP-1005.')">👤 Nhân viên EMP-1005</div>
      <div class="chip" onclick="quickAsk('Tạo ticket sự cố màn hình máy DT-031 bị chớp tắt, mức ưu tiên high.')">🎫 Tạo ticket DT-031</div>
    </div>

    <footer>
      <input type="text" id="user-input" class="input-box" placeholder="Nhập câu hỏi hỗ trợ kỹ thuật..." onkeypress="handleKey(event)" />
      <button id="send-btn" class="send-btn" onclick="sendMessage()">Gửi</button>
    </footer>
  </main>

  <script>
    let currentVersion = "v0";
    let chatHistory = [];

    function setVersion(ver) {
      currentVersion = ver;
      document.querySelectorAll('.version-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.includes(ver));
      });
      addSystemNotification(`Đã chuyển sang phiên bản <b>${ver}</b>`);
    }

    function switchProvider() {
      const provider = document.getElementById('provider-select').value;
      addSystemNotification(`Đã đổi provider sang: <b>${provider}</b>`);
    }

    function addSystemNotification(html) {
      const history = document.getElementById('chat-history');
      const div = document.createElement('div');
      div.style.cssText = "text-align: center; font-size: 0.78rem; color: #94a3b8; margin: 4px 0;";
      div.innerHTML = html;
      history.appendChild(div);
      history.scrollTop = history.scrollHeight;
    }

    function quickAsk(text) {
      document.getElementById('user-input').value = text;
      sendMessage();
    }

    function handleKey(e) {
      if (e.key === 'Enter') sendMessage();
    }

    async function sendMessage() {
      const input = document.getElementById('user-input');
      const text = input.value.trim();
      if (!text) return;

      const provider = document.getElementById('provider-select').value;
      const historyDiv = document.getElementById('chat-history');
      const sendBtn = document.getElementById('send-btn');

      // Append User message
      const userMsg = document.createElement('div');
      userMsg.className = 'message user';
      userMsg.innerHTML = `<div class="sender-label">Bạn</div><div class="bubble">${escapeHtml(text)}</div>`;
      historyDiv.appendChild(userMsg);
      input.value = '';
      sendBtn.disabled = true;

      // Loading
      const loading = document.createElement('div');
      loading.className = 'loading-indicator';
      loading.id = 'loading-ind';
      loading.innerHTML = `⏳ Agent [${currentVersion}] đang phân tích & định tuyến công cụ...`;
      historyDiv.appendChild(loading);
      historyDiv.scrollTop = historyDiv.scrollHeight;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: text,
            version: currentVersion,
            provider: provider,
            history: chatHistory
          })
        });
        const data = await res.json();
        loading.remove();

        // Render Tool Calls (if any)
        if (data.tool_events && data.tool_events.length > 0) {
          data.tool_events.forEach(ev => {
            const isErr = ev.result && (ev.result.error || ev.result.status === 'error');
            const toolCard = document.createElement('div');
            toolCard.className = 'tool-card';
            toolCard.innerHTML = `
              <div class="tool-header">
                <div>⚙️ TOOL CALL [${currentVersion}]: <span class="tool-name">${ev.tool}</span></div>
                <div style="font-size:0.75rem; color:${isErr ? 'var(--error)' : 'var(--success)'}; font-weight:700">
                  ${isErr ? '❌ LỖI / THẤT BẠI' : '✅ THỰC THI THÀNH CÔNG'}
                </div>
              </div>
              <div class="tool-body">
                <div>
                  <div class="tool-section-title input">📥 Input Payload:</div>
                  <pre class="code-block">${escapeHtml(JSON.stringify(ev.args, null, 2))}</pre>
                </div>
                <div>
                  <div class="tool-section-title ${isErr ? 'error' : 'result'}">${isErr ? '❌ Tool Error:' : '📤 Tool Output:'}</div>
                  <pre class="code-block">${escapeHtml(JSON.stringify(ev.result, null, 2))}</pre>
                </div>
              </div>
            `;
            historyDiv.appendChild(toolCard);
          });
        }

        // Render Assistant text
        const agentMsg = document.createElement('div');
        agentMsg.className = 'message assistant';
        agentMsg.innerHTML = `
          <div class="sender-label">Agent [${currentVersion}] (${provider})</div>
          <div class="bubble">${formatMarkdown(data.assistant_text || '(Không có phản hồi dạng text)')}</div>
        `;
        historyDiv.appendChild(agentMsg);

        // Update memory history
        chatHistory.push({ role: 'user', content: text });
        chatHistory.push({ role: 'assistant', content: data.assistant_text || '' });

      } catch (err) {
        if (document.getElementById('loading-ind')) document.getElementById('loading-ind').remove();
        const errMsg = document.createElement('div');
        errMsg.className = 'message assistant';
        errMsg.innerHTML = `<div class="sender-label">Hệ thống</div><div class="bubble" style="color:red">Lỗi kết nối API: ${escapeHtml(err.message)}</div>`;
        historyDiv.appendChild(errMsg);
      } finally {
        sendBtn.disabled = false;
        historyDiv.scrollTop = historyDiv.scrollHeight;
        input.focus();
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    function formatMarkdown(str) {
      let s = escapeHtml(str);
      // bold
      s = s.replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>');
      return s;
    }
  </script>
</body>
</html>
"""


class DemoHTTPHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        else:
            super().do_GET()

    def do_POST(self) -> None:
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body)
                user_message = payload.get("message", "")
                version = payload.get("version", "v0")
                provider_name = payload.get("provider", "openrouter")
                history = payload.get("history", [])

                # Run Agent Loop
                system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
                tool_declarations = load_tool_declarations(TOOLS_PATH)
                openai_tools = to_openai_tools(tool_declarations)
                provider = make_provider(provider_name)
                artifact_version = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)

                messages = [
                    {"role": "system", "content": system_prompt},
                    *trim_history(history, 5),
                    {"role": "user", "content": user_message},
                ]

                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=getattr(provider, "default_model", None),
                    max_tool_rounds=4,
                    version=version,
                )

                # Save transcript entry
                timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
                transcript_id = f"webdemo_{version}_{provider_name}_{timestamp}"
                transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"

                transcript = {
                    "transcript_id": transcript_id,
                    "version": version,
                    **artifact_version_dict(artifact_version),
                    "provider": provider_name,
                    "model": getattr(provider, "default_model", None),
                    "turns": [
                        {
                            "user": user_message,
                            "assistant_text": result.get("assistant_text"),
                            "status": result.get("status"),
                            "tool_events": result.get("tool_events", []),
                        }
                    ],
                }
                write_transcript(transcript_path, transcript)

                # Response JSON
                resp_data = {
                    "status": "success",
                    "assistant_text": result.get("assistant_text"),
                    "tool_events": result.get("tool_events", []),
                    "transcript_id": transcript_id,
                }

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(resp_data, ensure_ascii=False).encode("utf-8"))

            except Exception as exc:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                err_payload = {"status": "error", "message": str(exc), "error_type": type(exc).__name__}
                self.wfile.write(json.dumps(err_payload, ensure_ascii=False).encode("utf-8"))


def main() -> None:
    server = ThreadingHTTPServer(("localhost", PORT), DemoHTTPHandler)
    url = f"http://localhost:{PORT}"
    print("=" * 65)
    print(" 🌟 IT HELPDESK AGENT — LIGHT-THEMED WEB DEMO UI")
    print(f" 🌐 Địa chỉ truy cập: {url}")
    print(" 💡 Nhấn Ctrl + C để dừng server.")
    print("=" * 65)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng Web UI server.")
        server.server_close()


if __name__ == "__main__":
    main()
