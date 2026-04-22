---
title: Sổ lệnh
source_url: https://wiki.turtletrading.vn/concepts/so_lenh
tags: []
backlinks: []
related_count: 3
crawled_at: '2026-04-21T05:01:10Z'
---

# Sổ lệnh

Sổ lệnh là cấu trúc hiển thị các lệnh chờ theo từng mức giá, gồm **cột BID** (giá chào mua) và **cột ASK** (giá chào bán). Khi thực hiện lệnh thị trường, giá nhận được/giá phải trả phụ thuộc vào mức bid/ask tốt nhất hiện có trong sổ lệnh [📄 Nguồn](https://www.turtletrading.vn/2025/01/tai-sao-gia-di-chuyen.html).

## Liên kết & Insight

Sổ lệnh là nơi “đặt nền” cho việc giá thực tế được khớp, vì bid/ask tốt nhất trong sổ lệnh quyết định taker sẽ nhận được giá nào và phải trả giá nào. Khi [spread](../concepts/spread) mở rộng hoặc thanh khoản trong sổ mỏng, đường đi của giá thường kém trơn tru hơn, khiến kết quả giao dịch dễ lệch khỏi kỳ vọng. Insight chính là: muốn hiểu hiệu suất chiến lược, bạn không chỉ nhìn chart mà cần liên hệ sổ lệnh với [taker](../concepts/taker) và mức [spread](../concepts/spread) để biết lệnh của mình đang “ăn” thanh khoản ở đâu.

## Liên quan

* [gia\_bid\_ask](../concepts/gia_bid_ask): bid/ask tốt nhất được lấy từ sổ lệnh.
* [spread](../concepts/spread): chênh lệch giữa bid và ask tốt nhất.
* thanh khoan: số lượng lệnh chờ trong sổ lệnh quyết định độ “dễ” để giá di chuyển.
* [taker](../concepts/taker): taker lấy đi thanh khoản trong sổ lệnh.