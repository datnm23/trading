---
title: Độ co hẹp kết quả
source_url: https://wiki.turtletrading.vn/concepts/do_co_hop_ket_qua
tags: []
backlinks: []
related_count: 2
crawled_at: '2026-04-21T05:00:12Z'
---

# Độ co hẹp kết quả

Độ co hẹp kết quả mô tả hiện tượng khi tăng số lệnh [backtest](../concepts/backtest) thì phân phối các chỉ số hiệu suất sẽ hội tụ và dao động giảm. Điều này liên quan trực tiếp đến việc ước lượng từ mẫu lớn ổn định hơn mẫu nhỏ. Bạn có thể dùng khái niệm này để hiểu vì sao [entropy\_tang\_len](../concepts/entropy_tang_len) thường đi kèm với sự “chắc” hơn của ước lượng.

## Liên kết & Insight

Độ co hẹp kết quả giải thích vì sao khi bạn tăng số lệnh trong [backtest](../concepts/backtest), các chỉ số như lợi nhuận hay tỷ lệ thắng bắt đầu “hội tụ” và dao động giảm. Nó liên kết chặt với ý tưởng rằng ước lượng từ mẫu lớn ổn định hơn mẫu nhỏ, nên khi phân tích độ chắc của chiến lược bạn sẽ thấy cảm giác “chắc tay” tăng lên. Insight cốt lõi là: đừng tin vào một kết quả đẹp từ mẫu ít lệnh; hãy nhìn sự hội tụ theo quy mô mẫu, vì đó mới là dấu hiệu đánh giá đáng tin hơn.