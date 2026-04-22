---
title: Kiểm tra độ ổn định toàn phần
source_url: https://wiki.turtletrading.vn/concepts/toan_bo_kiem_tra_do_on_dinh
tags: []
backlinks: []
related_count: 4
crawled_at: '2026-04-21T05:01:22Z'
---

# Kiểm tra độ ổn định toàn phần

Kiểm tra độ ổn định toàn phần là cách đánh giá hệ thống bằng cách thay đổi tham số trong một dải hợp lý và quan sát xem hiệu suất có giữ được lợi thế hay không. Nếu chiến lược chỉ tốt ở một điểm tham số cụ thể, đó là dấu hiệu dễ bị quá khớp; ngược lại, nếu hiệu suất duy trì tốt trên một vùng rộng thì kết luận đáng tin hơn. Trong chương này, tham số [dừng lỗ](../concepts/dung_lo) theo bội số ATR được quét từ thấp đến cao để tìm vùng ổn định. [backtest\_chinh\_xac](../concepts/backtest_chinh_xac) và [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam) nên được hiểu như hai lớp kiểm tra khác nhau khi nói về độ tin cậy.

## Liên kết & Insight

Kiểm tra độ ổn định toàn phần liên kết với [backtest\_chinh\_xac](../concepts/backtest_chinh_xac) và [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam) vì nó không chỉ hỏi “lãi không”, mà hỏi “lãi có bền khi thay tham số không”. Bằng cách quét vùng tham số hợp lý (ví dụ dừng lỗ theo bội số ATR), bạn giảm nguy cơ nhầm chiến lược [may mắn](../concepts/may_man) với chiến lược có cấu trúc. Insight cốt lõi là: nếu hiệu suất chỉ đứng vững ở một điểm tham số, đó thường là dấu hiệu quá khớp; còn vùng ổn định rộng mới đáng tin hơn.