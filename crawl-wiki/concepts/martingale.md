---
title: Martingale
source_url: https://wiki.turtletrading.vn/concepts/martingale
tags: []
backlinks: []
related_count: 8
crawled_at: '2026-04-21T05:00:45Z'
---

# Martingale

Martingale là cách [quản lý vốn](../concepts/quan_ly_von) được nhắc đến như một ví dụ chiến lược không đặt cắt lỗ, nên không kiểm soát được rủi ro tối đa và [drawdown](../concepts/drawdown) tối đa. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)

## Hệ quả rủi ro

* Do không giới hạn mức rủi ro tối đa, martingale có thể “gồng lỗ đến vô cực”, làm cho việc đo lường [drawdown](../concepts/drawdown) tối đa không rõ ràng. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)

Martingale tạo ra [rủi ro đuôi](../concepts/tail_risk) khó kiểm soát vì chuỗi thua có thể kéo dài lâu hơn giả định, khiến mức rủi ro tích lũy tăng theo cấp số nhân. Trên đồ thị vốn, bạn thường thấy các nhịp sụt nhọn rồi hồi phục nhanh—nhưng chính “chuỗi thua hiếm nhưng rất dài” mới là thứ quyết định sự phá sản.

## Liên kết & Insight

Martingale liên kết chặt với [quan\_ly\_von](../concepts/quan_ly_von) và đặc biệt là bài toán kiểm soát [max\_drawdown](../concepts/max_drawdown): vì không đặt giới hạn rủi ro tối đa, nên chuỗi thua có thể kéo dài đủ lâu để làm drawdown “không có trần”. Điểm insight là martingale thường trông như chỉ tạo ra các nhịp sụt rồi hồi nhanh, nhưng rủi ro thật nằm ở “đuôi” — chuỗi thua hiếm nhưng rất dài mới là thứ quyết định phá sản. Khi bạn thiếu cơ chế cắt rủi ro, việc đo lường và quản trị rủi ro tối đa trở nên mơ hồ.

## Liên quan

* [quan\_ly\_drawdown](../concepts/quan_ly_drawdown): cần giới hạn rủi ro để kiểm soát drawdown. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)
* [dung\_lo](../concepts/dung_lo): công cụ đối lập với [chiến lược không cắt lỗ](../concepts/chien_luoc_khong_cat_lo). [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)
* [dca](../concepts/dca): ví dụ khác cùng vấn đề không giới hạn rủi ro tối đa. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)