---
title: Sai số ước lượng
source_url: https://wiki.turtletrading.vn/concepts/estimation_error
tags: []
backlinks: []
related_count: 8
crawled_at: '2026-04-21T05:00:19Z'
---

# Sai số ước lượng

Sai số ước lượng là phần sai lệch do ta ước lượng các tham số (mean, variance, covariance, v.v.) từ dữ liệu hữu hạn. Trong [Extremistan](../concepts/extremistan), các tham số này có thể không hội tụ, nên sai số ước lượng trở nên lớn và dễ bị tối ưu hóa khuếch đại. [📄 Nguồn](https://www.turtletrading.vn/2026/01/ao-giac-toi-uu.html)

Bài viết nhấn mạnh rằng mô hình Markowitz cần mean/variance/covariance “đủ đúng”; nếu input sai do ước lượng, thuật toán sẽ dồn trọng số vào những thứ “đẹp trong quá khứ” nhưng thực chất là nhiễu/[may mắn](../concepts/may_man). [📄 Nguồn](https://www.turtletrading.vn/2026/01/ao-giac-toi-uu.html)

## Liên kết & Insight

Sai số ước lượng là lý do khiến các mô hình danh mục và chiến lược có thể “trông đúng” trên dữ liệu nhưng lại lệch khỏi thực tế, vì ta ước lượng mean/variance/covariance từ mẫu hữu hạn. Khi sai số này lớn, thuật toán tối ưu sẽ vô tình dồn trọng số vào những thứ chỉ đẹp do nhiễu hoặc [may mắn](../concepts/may_man), khiến kết quả bị [overfit vào quá khứ](../concepts/overfit_vao_qua_khu). Insight cốt lõi là: trong trading, mô hình chỉ đáng tin khi tham số đủ ổn định; nếu không, tối ưu hóa sẽ khuếch đại lỗi thay vì tạo ra edge.

## Liên quan

* [overfit\_vao\_qua\_khu](../concepts/overfit_vao_qua_khu): sai số ước lượng là một nguồn gốc của overfit.
* [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam): [backtest](../concepts/backtest) có thể đẹp do ước lượng sai nhưng [trùng hợp](../concepts/trung_hop).
* [optimizing\_in\_extremistan](../concepts/optimizing_in_extremistan): trong [Extremistan](../concepts/extremistan), sai số ước lượng càng dễ phá tối ưu.
* [tinh\_tu\_hoc](../concepts/tinh_tu_hoc): các công thức thống kê chỉ hữu dụng khi giả định hội tụ/ổn định thỏa.