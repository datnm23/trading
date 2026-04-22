---
title: Xác suất và khả năng (Likelihood)
source_url: https://wiki.turtletrading.vn/concepts/xac_suat_vs_kha_nang
tags: []
backlinks: []
related_count: 1
crawled_at: '2026-04-21T05:01:39Z'
---

# Xác suất và khả năng (Likelihood)

Trong thống kê, “xác suất” (Probability) mô tả mức độ xảy ra của một kết quả khi bạn đã biết mô hình trước. Ngược lại, “khả năng” (Likelihood) đo mức độ mô hình với các tham số cụ thể giải thích tốt dữ liệu đã quan sát đến đâu. Khi [backtest](../concepts/backtest), bạn thực chất đang dùng dữ liệu để ước lượng các tham số (ví dụ tỷ lệ thắng, R:R) và so sánh mô hình nào phù hợp dữ liệu hơn, nên cách hiểu “khả năng” giúp bạn đánh giá đúng mức độ chắc chắn của kết luận.

## Liên kết & Insight

Xác suất và khả năng giúp bạn hiểu khác nhau giữa “kết quả sẽ xảy ra thế nào” và “mô hình nào giải thích dữ liệu tốt hơn”. Khi bạn làm [backtest](../concepts/backtest), bạn không chỉ đếm thắng thua mà còn đang ước lượng tham số để xem chiến lược khớp dữ liệu đến mức nào. Insight chính là: một chiến lược có thể trông “xác suất cao” nhưng lại có “khả năng” thấp với dữ liệu quan sát; vì vậy cần đọc [backtest](../concepts/backtest) như bài toán phù hợp mô hình, không phải giấy chứng nhận chắc chắn.