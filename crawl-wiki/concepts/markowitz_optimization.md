---
title: Tối ưu Markowitz
source_url: https://wiki.turtletrading.vn/concepts/markowitz_optimization
tags: []
backlinks: []
related_count: 6
crawled_at: '2026-04-21T05:00:45Z'
---

# Tối ưu Markowitz

Tối ưu Markowitz là cách phân bổ danh mục dựa trên các tham số thống kê như mean, variance và covariance để tối đa hóa trade-off risk/return. [📄 Nguồn](https://www.turtletrading.vn/2026/01/ao-giac-toi-uu.html)

Trong bối cảnh [Extremistan](../concepts/extremistan), mean/variance/covariance có thể không hội tụ hoặc nhạy với outlier, khiến tối ưu hóa trở thành “tối ưu ảo giác” và có thể làm hiệu suất live tệ hơn [backtest](../concepts/backtest). [📄 Nguồn](https://www.turtletrading.vn/2026/01/ao-giac-toi-uu.html)

## Liên kết & Insight

Tối ưu Markowitz phân bổ danh mục bằng cách dùng mean/variance/covariance để cân bằng giữa kỳ vọng lợi nhuận và rủi ro. Trong môi trường [extremistan](../concepts/extremistan), các tham số thống kê này dễ không hội tụ hoặc bị outlier chi phối, khiến tối ưu hóa trở thành “ảo giác” và hiệu suất live lệch mạnh so với kỳ vọng từ [backtest](../concepts/backtest). Insight cốt lõi là nếu dữ liệu đuôi dày và [sai số ước lượng](../concepts/estimation_error) lớn, bạn không nên tin vào con số tối ưu như một sự thật—hãy nghi ngờ tính ổn định của tham số và kiểm tra độ bền trước nhiễu.

## Liên quan

* [optimizing\_in\_extremistan](../concepts/optimizing_in_extremistan): giải thích vì sao Markowitz dễ gãy trong thị trường đuôi dày.
* [estimation\_error](../concepts/estimation_error): Markowitz nhạy với sai số ước lượng tham số.
* [phan\_phoi\_duoi\_beo](../concepts/phan_phoi_duoi_beo): đuôi dày làm variance/covariance kém ổn định.
* [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam): [backtest](../concepts/backtest) có thể bị “đánh lừa” bởi nhiễu.