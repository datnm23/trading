---
title: Độ rộng mẫu backtest
source_url: https://wiki.turtletrading.vn/concepts/do_rong_mau_backtest
tags: []
backlinks: []
related_count: 2
crawled_at: '2026-04-21T05:00:12Z'
---

# Độ rộng mẫu backtest

Độ rộng mẫu là thước đo mức độ [backtest](../concepts/backtest) bao phủ đủ nhiều lệnh, nhiều giai đoạn và/hoặc nhiều thị trường để giảm sai lệch do ngẫu nhiên. Mẫu quá hẹp khiến các ước lượng như [tỷ lệ thắng và R:R](../concepts/ty_le_thang_va_rr) có biên dao động lớn, nên kết quả có thể thay đổi mạnh khi chạy ngoài mẫu. Khi tăng độ rộng mẫu, bạn thường thấy hiệu suất hội tụ và đánh giá trở nên đáng tin hơn, dù vẫn không thể đảm bảo chiến lược sẽ luôn hoạt động.

## Liên kết & Insight

Độ rộng mẫu backtest nói về việc bạn đã bao phủ đủ nhiều lệnh, giai đoạn và thị trường hay chưa để giảm nhiễu ngẫu nhiên. Khi mẫu quá hẹp, các ước lượng như [tỷ lệ thắng và R:R](../concepts/ty_le_thang_va_rr) sẽ dao động mạnh và dễ “đẹp giả”, khiến bạn bị ảo tưởng về độ bền của chiến lược ngoài mẫu. Insight cốt lõi là: tăng độ rộng mẫu giúp hiệu suất hội tụ và đánh giá đáng tin hơn, nhưng vẫn không biến backtest thành bảo chứng.