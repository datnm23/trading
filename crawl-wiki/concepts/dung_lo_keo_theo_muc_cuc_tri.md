---
title: Dừng lỗ kéo theo mức cực trị
source_url: https://wiki.turtletrading.vn/concepts/dung_lo_keo_theo_muc_cuc_tri
tags: []
backlinks: []
related_count: 4
crawled_at: '2026-04-21T05:00:16Z'
---

# Dừng lỗ kéo theo mức cực trị

> Thuộc về
>
> * [Dừng lỗ](../concepts/dung_lo)

[Dừng lỗ](../concepts/dung_lo) kéo theo theo cực trị là cơ chế cập nhật stop-loss dựa trên mức giá cực trị của nến trên khung thời gian lớn (ví dụ đáy gần nhất khi đang lệnh mua, hoặc đỉnh gần nhất khi đang lệnh bán). Cách này giúp “khóa” lợi nhuận dần theo thời gian, đồng thời vẫn cho phép vị thế thở trong giai đoạn xu hướng còn tiếp diễn. Nó thường được kết hợp với dừng lỗ ban đầu đặt theo [atr](../concepts/atr). [chien\_luoc\_cat\_lo\_nghiem\_ngat](../chien_luoc_cat_lo_nghiem_ngat) và [drawdown](../concepts/drawdown) có thể được cải thiện nhờ kỷ luật thoát lệnh.

## Liên kết & Insight

Dừng lỗ kéo theo mức cực trị kết nối trực tiếp với [dung\_lo](../concepts/dung_lo) và thường được “neo” thêm bằng [atr](../concepts/atr) để vừa có điểm cắt ban đầu hợp lý vừa có cơ chế khóa lợi nhuận khi giá đi theo xu hướng. Thay vì chốt cứng ngay, stop được cập nhật theo đáy/đỉnh gần nhất giúp vị thế có không gian thở nhưng vẫn giới hạn phần mất lại khi xu hướng gãy. Insight cốt lõi là: kỷ luật thoát lệnh theo cấu trúc giá giúp giảm cảm xúc và cải thiện chất lượng quản trị rủi ro theo thời gian.