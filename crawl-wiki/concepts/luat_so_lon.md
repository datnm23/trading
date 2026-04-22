---
title: Luật số lớn
source_url: https://wiki.turtletrading.vn/concepts/luat_so_lon
tags: []
backlinks: []
related_count: 5
crawled_at: '2026-04-21T05:00:44Z'
---

# Luật số lớn

Luật số lớn nói rằng các phần tử ngẫu nhiên đơn lẻ có thể hành xử ngẫu nhiên, nhưng một tập hợp đủ lớn sẽ tạo ra quy luật. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Trong [backtest](../concepts/backtest), nếu chỉ có vài trăm lệnh thì kết quả có thể chủ yếu là ngẫu nhiên; nhưng khi [backtest](../concepts/backtest) tới hàng chục/hàng trăm nghìn lệnh trên nhiều thị trường, khả năng kết quả chỉ do ngẫu nhiên sẽ giảm mạnh. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

## Liên kết & Insight

Luật số lớn giải thích vì sao một chiến lược có thể trông “có quy luật” khi chạy đủ nhiều mẫu, dù từng lệnh riêng lẻ vẫn mang tính ngẫu nhiên. Vì vậy, khi đánh giá qua [backtest](../concepts/backtest), số lượng lệnh và phạm vi thị trường càng lớn thì xác suất kết quả chỉ do [may mắn](../concepts/may_man) càng giảm, thay vì bị chi phối bởi tiếng ồn của [phan\_phoi\_ngau\_nhien](../concepts/phan_phoi_ngau_nhien). Insight cốt lõi là đừng vội kết luận từ vài trăm lệnh; hãy nhìn chiến lược như một thống kê cần đủ cỡ mẫu để lộ ra hành vi thật.

## Liên quan

* [phan\_phoi\_ngau\_nhien](../concepts/phan_phoi_ngau_nhien)
* [so\_mau\_du\_lon](../concepts/so_mau_du_lon)
* [khong\_ergodic\_trading](../concepts/khong_ergodic_trading)