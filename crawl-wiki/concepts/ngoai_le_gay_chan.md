---
title: Ngoại lệ gãy chân
source_url: https://wiki.turtletrading.vn/concepts/ngoai_le_gay_chan
tags: []
backlinks: []
related_count: 6
crawled_at: '2026-04-21T05:00:50Z'
---

# Ngoại lệ gãy chân

Ngoại lệ gãy chân (broken leg exception) là tình huống dữ liệu mới nằm **ngoài phân phối** mà mô hình đã học ([out of distribution](../concepts/out_of_distribution) - OOD), khiến dự đoán “đúng trong bình thường” nhưng thất bại khi gặp trường hợp hiếm và quan trọng. [📄 Nguồn](https://www.turtletrading.vn/2026/03/ngoai-le-gay-chan-van-e-cua-moi-mo-hinh.html)

Khái niệm này liên quan trực tiếp đến [out\_of\_distribution](../concepts/out_of_distribution) và [non\_stationarity](../concepts/non_stationarity): khi thế giới đổi trạng thái hoặc xuất hiện dữ liệu hiếm, mô hình nội suy từ quá khứ có thể trở nên sai lệch. Trong trading, các “cú gãy chân ngoại lệ” thường là [tail\_event](../concepts/tail_event)/[tail\_risk](../concepts/tail_risk) làm hệ thống tự động sụp đổ. [📄 Nguồn](https://www.turtletrading.vn/2026/03/ngoai-le-gay-chan-van-e-cua-moi-mo-hinh.html)

## Liên kết & Insight

Ngoại lệ gãy chân mô tả lúc mô hình hoặc chiến lược tưởng “đang đúng quy luật” nhưng gặp dữ liệu hiếm nằm ngoài những gì nó từng học, nên dự đoán sụp đổ. Nó gắn với [out\_of\_distribution](../concepts/out_of_distribution) và [non\_stationarity](../concepts/non_stationarity) vì thị trường đổi trạng thái hoặc xuất hiện sự kiện hiếm khiến kỳ vọng từ quá khứ không còn dùng được. Trong trading, các cú gãy chân thường trùng với [tail\_risk](../concepts/tail_risk)/[tail\_event](../concepts/tail_event), nên insight cốt lõi là: đừng chỉ tối ưu theo trung bình—hãy thiết kế để chịu được phần đuôi xấu, vì [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam) rằng [quá khứ sẽ lặp lại](../concepts/qua_khu_se_lap_lai).

## Liên quan

* [out\_of\_distribution](../concepts/out_of_distribution)
* [tail\_risk](../concepts/tail_risk)
* [tail\_event](../concepts/tail_event)
* [non\_stationarity](../concepts/non_stationarity)
* [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam)