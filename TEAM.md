# TEAM — Day04, K4-L3B

**Làm nhóm.** Mỗi người tự viết và commit phần INDIVIDUAL của mình.

## Thông tin bài nộp

- Tên nhóm: **Nhóm T149**
- Người đại diện / MSSV: **Trần Đình Hinh / 2A202602399**
- Tên repo: `K4-L3-DAY04-TranDinhHinh-2A202602399-PromptEngineeringToolCalling`
- URL repo, nhánh nộp, commit chốt:
  - URL: `https://github.com/hinhtran/K4-L3-DAY04-T149-PromptEngineeringToolCalling`
  - Nhánh nộp: `main`
  - Commit chốt: `a7cf773`
- Deadline áp dụng và link thông báo đổi hạn nếu có: 23:59 ngày làm lab, Asia/Ho_Chi_Minh (UTC+07:00)

## Thành viên

| Họ và tên | MSSV | GitHub | Vai trò và công việc | File/commit/PR |
|---|---|---|---|---|
| **Trần Đình Hinh** | 2A202602399 | `hinhtran` | **Track A Lead**: Tối ưu Prompt qua v0–v3, tinh chỉnh schema tools.yaml, thực nghiệm bộ base và 12 ca an toàn adversarial | `508af63` (`artifacts/system_prompt.md`, `artifacts/version_log.csv`, `runs/`) |
| **Trần Tuần Cường** | 2A202602717 | `CuongTT-04` | **Track B Lead**: Thiết kế 10 test case nhóm (`eval_group.json`), phát triển Web Demo UI sáng màu, xây dựng Bonus Tool (`check_hardware_warranty`) và thu thập transcripts | `55a17cd`, PR #1 (`a7cf773`) (`data/eval_group.json`, `web_chat.py`, `chat.py`, `tools/check_hardware_warranty/`, `transcripts/`) |

## Nhận xét chung

- **Kết quả và bằng chứng**: Nhóm đã hoàn thành xuất sắc 100% mục tiêu của bài lab bao gồm 90 điểm phần chung và trọn vẹn 10 điểm Bonus kỹ thuật mở rộng.
  - Baseline v0 đạt độ chính xác ~76.7%, cải thiện qua các vòng v1, v2 lên 100% ở v3 với các rào chắn bảo vệ an toàn dữ liệu.
  - Bộ 10 ca nhóm (`eval_group.json`) đạt chuẩn schema, đo lường thành công với 0 lỗi provider (`runs/v0_B_group_openrouter_20260915T203332582455.json`).
  - Đã có đầy đủ 4 kịch bản transcript trong `starter_v0/transcripts/` và script kiểm thử tự động cho công cụ bonus `scripts/test_bonus_tool.py`.
- **Thay đổi hiệu quả nhất**: Việc bổ sung quy tắc xử lý thiếu thông tin (`clarify`) kết hợp siết chặt ranh giới xác nhận tạo ticket và phân định rõ giữa kiểm tra dịch vụ chung vs thiết bị cá nhân trong `system_prompt.md`.
- **Giới hạn còn lại**: Agent vẫn dựa trên việc nạp toàn bộ lịch sử hội thoại gần nhất (trượt 5 lượt). Khi các cuộc hội thoại kéo dài hàng chục lượt, cần áp dụng tóm tắt ngữ cảnh tự động (Summary Memory Buffer) để tiết kiệm token và tránh phân mảnh thông tin.
- **Cách phân công và tích hợp**: Phân tách rõ ràng thành 2 Track làm việc độc lập trên 2 branch (`feat/prompt-optimization` và `feat/eval-group-ui`), không chạm chéo file của nhau. Tích hợp thông qua Pull Request trên GitHub sạch sẽ, không xảy ra bất kỳ xung đột mã nguồn nào.

---

## INDIVIDUAL

### Trần Đình Hinh — 2A202602399

- **Phần việc và file/commit/PR**:
  - Phụ trách Track A: Nghiên cứu baseline v0, đặt giả thuyết cải tiến prompt qua các vòng lặp v1, v2, v3.
  - Sửa đổi các file: `starter_v0/artifacts/system_prompt.md`, `starter_v0/artifacts/tools.yaml`, `starter_v0/artifacts/version_log.csv`.
  - Đánh giá bộ 12 ca an toàn adversarial trong `data/eval_adversarial.json` và phân tích chuyên sâu 3 ca tấn công trong báo cáo.
  - Commit chính: `508af63` (`feat(track-a): complete core agent prompt engineering, tools schema and v0-v3 evaluations`).
- **Quyết định, khó khăn và cách xử lý**:
  - *Khó khăn:* Model hay bị nhầm lẫn giữa kiểm tra trạng thái một máy cá nhân với trạng thái dịch vụ dùng chung của công ty (ví dụ: máy lỗi Wi-Fi nhưng lại đi check trạng thái trạm phát Wi-Fi toàn công ty).
  - *Xử lý:* Định nghĩa tường minh trong `system_prompt.md` quy tắc: "Bất kỳ câu hỏi nào đề cập đến một thiết bị cụ thể (laptop, desktop) hoặc có Asset ID phải dùng `inspect_device`; chỉ dùng `check_service_status` khi câu hỏi hỏi về hạ tầng chung".
- **Điều đã học**: Hiểu sâu sắc về cơ chế Function Calling của LLM, cách thiết kế schema tham số để model không hallucinate, và kỹ thuật thiết lập ranh giới an toàn (Confirmation Boundary) trước các hành động ghi dữ liệu có side-effect.
- **AI/công cụ đã dùng và cách kiểm tra**: Sử dụng Antigravity IDE, Python venv, OpenRouter & Google Gemini API, script `run_eval.py` để kiểm tra độ chính xác sau mỗi vòng lặp prompt.
- **Thời điểm đã tự nộp URL repo chung trên VLearn**: 23:15 ngày 15/09/2026.

---

### Trần Tuần Cường — 2A202602717

- **Phần việc và file/commit/PR**:
  - Phụ trách Track B: Thiết kế 10 ca kiểm thử nhóm trong `starter_v0/data/eval_group.json` (5 câu đơn lượt + 5 câu đa lượt có đổi ý và bổ sung thông tin).
  - Nâng cấp giao diện dòng lệnh `starter_v0/chat.py` hiển thị trực quan thông tin phiên bản, tool call, input payload, tool output/lỗi.
  - Phát triển ứng dụng Web Demo UI sáng màu (`starter_v0/web_chat.py`) phục vụ trình diễn và thuyết trình với giảng viên.
  - Xây dựng hoàn chỉnh tính năng mở rộng Bonus 10 điểm: Công cụ tra cứu bảo hành phần cứng `check_hardware_warranty` (`tools/check_hardware_warranty/`, `scripts/test_bonus_tool.py`).
  - Ghi nhận và kiểm tra toàn bộ 4 file transcript thực tế theo rubric trong thư mục `starter_v0/transcripts/`.
  - Commit và PR: Commit `55a17cd`, PR #1 (`a7cf773`).
- **Quyết định, khó khăn và cách xử lý**:
  - *Khó khăn:* Ban đầu dùng API key Gemini gặp lỗi giới hạn tần suất 20 requests/ngày (429 Resource Exhausted) khiến việc chạy eval bị lỗi provider.
  - *Xử lý:* Chuyển đổi linh hoạt sang provider OpenRouter (`openai/gpt-4o-mini`) theo đúng khuyến nghị của đề bài, giúp chạy mượt mà toàn bộ 10 ca test nhóm và sinh transcript chuẩn với `provider_error_cases == 0`.
- **Điều đã học**: Nắm vững quy trình kiểm thử tự động cho LLM Agent, cách xử lý state và context trong hội thoại đa lượt (multi-turn), và cách xây dựng giao diện tương tác minh bạch các bước suy luận và gọi công cụ của Agent.
- **AI/công cụ đã dùng và cách kiểm tra**: Antigravity IDE, Git Bash, OpenRouter, Google AI Studio, trình duyệt web chạy local Web UI (`http://localhost:8000`).
- **Thời điểm đã tự nộp URL repo chung trên VLearn**: 23:20 ngày 15/09/2026.
