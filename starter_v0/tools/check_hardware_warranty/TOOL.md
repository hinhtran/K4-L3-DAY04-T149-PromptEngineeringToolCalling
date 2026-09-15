---
name: check_hardware_warranty
track: bonus
kind: local_inventory
provider: mock_device_inventory
requires_env: []
inputs: [asset_id]
outputs: [asset_id, model, manufacturer, purchase_date, warranty_until, is_under_warranty, warranty_status, days_remaining]
side_effect: false
requires_confirmation: false
---
# check_hardware_warranty

Tra cứu chi tiết trạng thái bảo hành phần cứng của một thiết bị công ty theo Asset ID.
Trả về hãng, model, ngày mua, ngày hết hạn bảo hành, trạng thái bảo hành (active / expiring_soon / expired) và số ngày còn lại tính theo mốc dữ liệu hệ thống.
Nếu Asset ID không tồn tại hoặc bỏ trống, trả về mã lỗi rõ ràng.
