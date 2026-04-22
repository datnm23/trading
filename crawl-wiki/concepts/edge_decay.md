---
title: Edge decay
source_url: https://wiki.turtletrading.vn/concepts/edge_decay
tags: []
backlinks: []
related_count: 8
crawled_at: '2026-04-21T05:00:18Z'
---

# Edge decay

Edge decay là hiện tượng lợi thế giao dịch bị mòn dần theo thời gian: khi càng nhiều người biết cùng một mô hình/setup và cùng chạy vào, hiệu quả của setup đó giảm [📄 Nguồn](https://www.turtletrading.vn/2026/04/ai-co-giet-thi-truong-khong.html). Hiện tượng này không cần AI để xuất hiện; nó đã tồn tại từ trước kỷ nguyên LLM, và có thể bị đẩy nhanh hơn nhờ khả năng [backtest](../concepts/backtest)/copy chiến lược nhanh [📄 Nguồn](https://www.turtletrading.vn/2026/04/ai-co-giet-thi-truong-khong.html).

## Dấu hiệu thực hành

* Chiến lược “breakout đơn giản” chạy lại trên đúng cặp có thể cho [drawdown](../concepts/drawdown) dài hơn và win rate mỏng hơn dù công thức không đổi [📄 Nguồn](https://www.turtletrading.vn/2026/04/ai-co-giet-thi-truong-khong.html).

## Liên kết

* Edge decay gắn với [edge\_bien\_mat](../concepts/edge_bien_mat) và [loi\_the\_edge](../concepts/loi_the_edge).
* Khi edge suy giảm, trader dễ đổi chiến lược theo cảm xúc trong [vong\_lap\_thay\_doi\_chien\_luoc](../concepts/vong_lap_thay_doi_chien_luoc).
* [Kiểm chứng bằng dữ liệu](../concepts/kiem_chung_bang_du_lieu) cần tránh ảo giác “[quá khứ sẽ lặp lại](../concepts/qua_khu_se_lap_lai)” qua [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam).

## Liên kết & Insight

Edge decay mô tả việc “lợi thế” không đứng yên: khi một setup được nhiều người nhận ra và cùng chạy, thị trường sẽ điều chỉnh làm hiệu quả giảm dần theo thời gian. Nó liên kết chặt với [edge\_bien\_mat](../concepts/edge_bien_mat) vì lợi thế thường dựa trên độ hiếm thông tin/khả năng khai thác, và khi độ hiếm mất đi thì edge mòn. Insight chính là đừng coi backtest hay kết quả quá khứ là giấy thông hành; hãy xem edge như thứ có tuổi thọ và kiểm chứng lại liên tục để tránh ảo giác “quá khứ sẽ lặp lại” qua [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam).