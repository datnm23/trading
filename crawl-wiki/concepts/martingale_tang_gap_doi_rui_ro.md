---
title: Martingale tăng gấp đôi rủi ro
source_url: https://wiki.turtletrading.vn/concepts/martingale_tang_gap_doi_rui_ro
tags: []
backlinks: []
related_count: 5
crawled_at: '2026-04-21T05:00:45Z'
---

# Martingale tăng gấp đôi rủi ro

> Thuộc về
>
> * [Martingale](../concepts/martingale)

Martingale là chiến lược trong đó **tăng gấp đôi rủi ro sau mỗi lần thua** (dù có thể vẫn dùng [dung\_lo](../concepts/dung_lo)), dựa trên giả định rằng chuỗi thua sẽ không kéo dài vô hạn [📄 Nguồn](https://www.turtletrading.vn/2025/05/chen-thanh-va-rui-ro-uoi-trong-giao-dich.html).

Bài viết nhấn mạnh rủi ro thực tế: chuỗi thua có thể kéo dài hơn dự kiến, làm rủi ro trên một lệnh tăng theo lũy thừa (ví dụ 30 lần thua liên tiếp dẫn tới tăng rủi ro rất lớn), và [rủi ro đuôi](../concepts/tail_risk) trở nên **không thể đo lường/kiểm soát** [📄 Nguồn](https://www.turtletrading.vn/2025/05/chen-thanh-va-rui-ro-uoi-trong-giao-dich.html).

## Liên kết & Insight

Martingale tăng gấp đôi rủi ro là phiên bản đẩy mạnh của [martingale](../concepts/martingale), nơi mỗi lần thua làm rủi ro tăng theo lũy thừa, khiến [tail\_risk](../concepts/tail_risk) trở thành thứ khó kiểm soát nhất. Quan hệ cốt lõi nằm ở chỗ: giả định chuỗi thua sẽ “dừng sớm” thường không đúng trong thực tế, và khi chuỗi thua kéo dài hơn kỳ vọng thì rủi ro tích lũy phình ra rất nhanh. Insight chính là đừng nhầm giữa “xác suất thắng lại” và “khả năng sống sót”: bạn có thể đúng về kỳ vọng dài hạn nhưng vẫn chết vì chuỗi thua đủ dài.

## Liên quan

* [martingale](../concepts/martingale)
* [tail\_risk](../concepts/tail_risk)
* [risk\_of\_ruin](../concepts/risk_of_ruin)
* [duoi\_bat\_dinh](../concepts/duoi_bat_dinh)