---
title: Biến đổi theo thời gian
source_url: https://wiki.turtletrading.vn/concepts/tai_bien_doi_theo_thoi_gian
tags: []
backlinks: []
related_count: 9
crawled_at: '2026-04-21T05:01:12Z'
---

# Biến đổi theo thời gian

Biến đổi theo thời gian là việc các quan hệ/“hàm con” trong mô hình giá không bất biến mà liên tục thay đổi theo thời gian [📄 Nguồn](https://www.turtletrading.vn/2025/08/tai-sao-du-oan-gia-thi-truong-lai-kho.html).

Bài viết chỉ ra các giả định sai thường gặp khi lập mô hình: coi [history\_price](../concepts/history_price), [order\_flow](../concepts/order_flow) và [macro](../concepts/macro) là bất biến; thực tế chúng thay đổi khi hành vi đám đông đổi, bot/AI khai thác cùng chiến lược, hoặc chính sách/kỳ vọng thị trường tái định nghĩa [📄 Nguồn](https://www.turtletrading.vn/2025/08/tai-sao-du-oan-gia-thi-truong-lai-kho.html).

## Liên kết & Insight

“Biến đổi theo thời gian” gắn với [black\_swan](../concepts/black_swan) và các sai lầm mô hình ở chỗ: quan hệ trong giá không đứng yên, nên mọi giả định “bất biến” về [history\_price](../concepts/history_price) hay [order\_flow](../concepts/order_flow) đều có thể sụp khi hành vi đám đông hoặc chính sách thay đổi. Nó cũng giải thích vì sao [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam): quá khứ không cam kết giữ nguyên [luật chơi](../concepts/luat_choi) khi các hàm con liên tục được tái định nghĩa. Insight cốt lõi là: edge không phải là công thức cố định, mà là khả năng thích nghi với sự thay đổi của quan hệ theo thời gian.

## Liên quan

* [thi\_truong\_tien\_hoa](../concepts/thi_truong_tien_hoa): [thị trường tiến hóa](../concepts/thi_truong_tien_hoa) làm quan hệ cũ mất hiệu lực.
* [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam): quá khứ không đảm bảo tương lai khi quan hệ biến đổi.
* [edge\_phu\_thuoc\_thi\_truong](../concepts/edge_phu_thuoc_thi_truong): lợi thế phụ thuộc trạng thái thị trường.
* [khong\_the\_tien\_doan](../concepts/khong_the_tien_doan): biến đổi theo thời gian làm dự đoán khó.