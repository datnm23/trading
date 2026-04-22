---
title: Ngoại lệ gãy chân (OOD)
source_url: https://wiki.turtletrading.vn/concepts/broken_leg_exception
tags: []
backlinks: []
related_count: 3
crawled_at: '2026-04-21T04:59:56Z'
---

# Ngoại lệ gãy chân (OOD)

[Ngoại lệ gãy chân](../concepts/ngoai_le_gay_chan) là tình huống dữ liệu/hoàn cảnh mới nằm ngoài phân phối mà mô hình đã học. Trong trading, nó tương ứng với việc [cấu trúc thị trường](../concepts/cau_truc_thi_truong) đổi trạng thái khiến các tín hiệu quen thuộc mất hiệu lực. Khi gặp [regime\_shift](../concepts/regime_shift), bạn nên nghi ngờ giả định cũ và ưu tiên quản trị rủi ro hơn là bám mô hình.

## Liên kết & Insight

Ngoại lệ gãy chân mô tả khoảnh khắc dữ liệu hoặc bối cảnh mới nằm ngoài thứ mà mô hình/chiến lược đã quen, khiến tín hiệu cũ mất tác dụng. Trong trading, điều này thường trùng với [regime\_shift](../concepts/regime_shift)—khi cấu trúc thị trường đổi trạng thái, các quy tắc tưởng đúng có thể trở thành sai. Insight cốt lõi là gặp OOD thì ưu tiên quản trị rủi ro và giảm niềm tin vào mô hình, vì vấn đề không nằm ở “bạn làm sai”, mà nằm ở việc thế giới đã đổi luật.