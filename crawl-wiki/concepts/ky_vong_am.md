---
title: Kỳ vọng âm
source_url: https://wiki.turtletrading.vn/concepts/ky_vong_am
tags: []
backlinks: []
related_count: 10
crawled_at: '2026-04-21T05:00:37Z'
---

# Kỳ vọng âm

Kỳ vọng âm (EV âm) là trạng thái mà chiến lược có toán học “định sẵn” xu hướng thua trong dài hạn, nên dù người giao dịch có bình tĩnh hay kỷ luật đến đâu thì kết quả cuối cùng vẫn có thể là lỗ. [📄 Nguồn](https://www.turtletrading.vn/2026/01/giai-ma-tam-ly-giao-dich.html)

Trong bài, ví dụ được mô tả theo dạng: winrate cao nhưng RR rất xấu (thắng nhỏ thua lớn) dẫn đến EV âm. [📄 Nguồn](https://www.turtletrading.vn/2026/01/giai-ma-tam-ly-giao-dich.html)

Kỳ vọng âm trong trading còn được hiểu là khi EV của chiến lược nhỏ hơn 0, nghĩa là về dài hạn chiến lược có xu hướng làm tài khoản đi xuống. [📄 Nguồn](https://www.turtletrading.vn/2025/08/cong-thuc-toan-hoc-thay-oi-cuoc-oi-minh.html)

Bài viết cũng dùng ví dụ các trò cờ bạc như lô, đề, casino: chúng được thiết kế với kỳ vọng âm, nên càng chơi càng chắc chắn mất tiền. [📄 Nguồn](https://www.turtletrading.vn/2025/08/cong-thuc-toan-hoc-thay-oi-cuoc-oi-minh.html)

## Liên kết & Insight

Kỳ vọng âm là “lỗi hệ thống” của một chiến lược: dù winrate có thể cao, nhưng RR và phân phối lãi–lỗ khiến [gia\_tri\_ky\_vong\_ev](../concepts/gia_tri_ky_vong_ev) < 0, nên dài hạn tài khoản có xu hướng đi xuống. Nó liên kết chặt với [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam) vì EV ước lượng có thể sai, nhưng nếu mô hình đúng thì kỷ luật cũng không cứu được. Insight cốt lõi là đừng nhầm cảm giác thắng nhiều với lợi thế bền vững—hãy kiểm EV trước khi tối ưu tâm lý hay tăng số lệnh.

## Liên quan

* [gia\_tri\_ky\_vong\_ev](../concepts/gia_tri_ky_vong_ev): EV là thước đo trung tâm để đánh giá chiến lược.
* [ky\_vong\_loi\_nhuan\_ev\_duong](../concepts/ky_vong_loi_nhuan_ev_duong): đối lập với EV âm.
* [ky\_vong\_loi\_nhuan\_qua\_cao](../concepts/ky_vong_loi_nhuan_qua_cao): kỳ vọng “nghe có vẻ an toàn” nhưng thực chất có thể là bẫy EV.
* [dung\_lo](../concepts/dung_lo): [quản lý rủi ro](../concepts/quan_ly_rui_ro) không biến EV âm thành EV dương, nhưng giúp sống sót qua [nhiễu ngắn hạn](../concepts/nhiu_ngan_han).
* [overtrading](../concepts/overtrading): kỳ vọng âm khiến việc tăng số lệnh thường làm xấu đi kết quả.
* [risk\_of\_ruin](../concepts/risk_of_ruin): kỳ vọng âm thường làm tăng xác suất “[cháy tài khoản](../concepts/chay_tai_khoan)”.
* [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam): EV/ước lượng có thể sai, nên cần [quản lý rủi ro](../concepts/quan_ly_rui_ro).

## Ghi chú

> Contradiction
>
> Bài viết nhấn mạnh “kỳ vọng âm” không thể bị tâm lý/kỷ luật cứu được; trong khi nhiều người thường đổ lỗi thất bại cho “tâm lý yếu”. [📄 Nguồn](https://www.turtletrading.vn/2026/01/giai-ma-tam-ly-giao-dich.html)