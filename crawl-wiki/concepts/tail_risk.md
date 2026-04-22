---
title: Tail risk
source_url: https://wiki.turtletrading.vn/concepts/tail_risk
tags: []
backlinks: []
related_count: 15
crawled_at: '2026-04-21T05:01:14Z'
---

# Tail risk

Tail risk (rủi ro đuôi) là rủi ro đến từ các biến cố cực đoan nằm ở “đuôi” của [phân phối lợi nhuận](../concepts/phan_phoi_loi_nhuan), thường xảy ra thường xuyên hơn kỳ vọng nếu dùng phân phối chuẩn [📄 Nguồn](https://www.turtletrading.vn/2025/03/ngau-nhien-hieu-qua-va-co-hoi-tu-xu.html).

Bài viết nhấn mạnh thị trường có xu hướng “[đuôi béo](../concepts/duoi_beo)”, khiến các biến động lớn xuất hiện nhiều hơn giả định chuẩn, từ đó làm mô hình dựa trên chuẩn dễ đánh giá thấp rủi ro [📄 Nguồn](https://www.turtletrading.vn/2025/03/ngau-nhien-hieu-qua-va-co-hoi-tu-xu.html).

Rủi ro đuôi không chỉ nằm ở việc thua lỗ lớn, mà còn ở việc xác suất xảy ra “lớn hơn nhiều so với bạn đã quan sát” trong mẫu dữ liệu. Vì vậy, một chiến lược có [kỳ vọng dương](../concepts/ky_vong_duong) trong [backtest](../concepts/backtest) vẫn có thể sụp đổ trong tương lai nếu [tail event](../concepts/tail_event) vượt quá phạm vi từng gặp.

Các kiểu chiến lược thường gặp [rủi ro đuôi trái](../concepts/rui_ro_duoi_trai) gồm [dca](../concepts/dca), [martingale](../concepts/martingale), hoặc [quản lý vốn](../concepts/quan_ly_von) gấp thếp — “đuôi” có thể khiến mọi lợi nhuận tích lũy biến mất. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

## Liên kết & Insight

Tail risk là kiểu rủi ro “đến từ đuôi” của phân phối lợi nhuận, nơi các cú sốc cực đoan xảy ra thường xuyên hơn bạn tưởng khi giả định phân phối chuẩn. Nó liên kết chặt với [phan\_phoi\_duoi\_beo](../concepts/phan_phoi_duoi_beo) và [duoi\_bat\_dinh](../concepts/duoi_bat_dinh) vì chính phần đuôi làm mô hình đánh giá thấp mức độ nguy hiểm. Insight cốt lõi là: ngay cả khi backtest cho kỳ vọng dương, bạn vẫn có thể “vỡ” khi tail event vượt xa những gì từng thấy trong dữ liệu, nên phải quản trị để sống sót qua đuôi.

## Liên quan

* [phan\_phoi\_duoi\_beo](../concepts/phan_phoi_duoi_beo): nguồn gốc thống kê của tail risk
* [duoi\_bat\_dinh](../concepts/duoi_bat_dinh): phần bất định trong mô hình
* [risk\_of\_ruin](../concepts/risk_of_ruin): tail risk có thể dẫn tới mất khả năng tồn tại
* [quan\_ly\_rui\_ro](../concepts/quan_ly_rui_ro): [quản lý rủi ro](../concepts/quan_ly_rui_ro) để sống sót qua đuôi
* [drawdown](../concepts/drawdown): tail event thường biểu hiện bằng drawdown nghiêm trọng
* [rui\_ro\_duoi\_trai](../concepts/rui_ro_duoi_trai): phần cực đoan bên trái của phân phối
* [duoi\_beo\_trong\_giao\_dich](../concepts/duoi_beo_trong_giao_dich): đuôi béo làm lợi thế khó bền