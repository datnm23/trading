---
title: Grid mean reversion
source_url: https://wiki.turtletrading.vn/concepts/grid_mean_reversion
tags: []
backlinks: []
related_count: 6
crawled_at: '2026-04-21T05:00:25Z'
---

# Grid mean reversion

Grid/mean reversion là kiểu hệ thống giao dịch thường có tỷ lệ thắng cao và equity “mượt” vì bám theo sự quay về trung bình. Tuy nhiên bài viết nhấn mạnh cấu trúc của nó giống “tối ưu trung bình”: bị chặn [đuôi phải](../concepts/duoi_phai) và không giới hạn đuôi trái, nên khi thị trường đi một mạch mạnh có thể mất phần lớn thành quả tích lũy [📄 Nguồn](https://www.turtletrading.vn/2026/02/cau-truc-thuc-su-cua-giau-co.html).

## Điểm rủi ro cấu trúc

* Khi xảy ra biến động mạnh theo một hướng, hệ thống có thể chịu đuôi trái lớn vì không có “trần” cho mất mát [📄 Nguồn](https://www.turtletrading.vn/2026/02/cau-truc-thuc-su-cua-giau-co.html).

## Liên kết & Insight

liên kết chặt với tư duy [tu\_duy\_trung\_binh](../concepts/tu_duy_trung_binh) vì nó khai thác việc giá có xu hướng quay về quanh một mức trung tâm. Khi [thị trường đi ngang](../concepts/thi_truong_di_ngang), hệ thống thường “êm” và tạo cảm giác ổn định, nhưng cấu trúc này lại phụ thuộc vào việc đuôi rủi ro có bị chặn hay không: nó dễ bị lộ [phan\_phoi\_duoi\_beo](../concepts/phan_phoi_duoi_beo) khi giá chạy một mạch mạnh. Insight chính là đừng chỉ nhìn tỷ lệ thắng hay đường equity mượt; hãy hỏi “đuôi trái của hệ thống bị giới hạn thế nào?”

## Liên quan

* [trend\_following](../concepts/trend_following)
* [tu\_duy\_trung\_binh](../concepts/tu_duy_trung_binh)
* [tail\_risk](../concepts/tail_risk)
* [phan\_phoi\_duoi\_beo](../concepts/phan_phoi_duoi_beo)