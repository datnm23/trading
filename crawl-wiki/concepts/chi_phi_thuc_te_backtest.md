---
title: Chi phí thực tế trong backtest
source_url: https://wiki.turtletrading.vn/concepts/chi_phi_thuc_te_backtest
tags: []
backlinks: []
related_count: 6
crawled_at: '2026-04-21T05:00:01Z'
---

# Chi phí thực tế trong backtest

[Backtest](../concepts/backtest) thường lạc quan hơn thực tế vì dữ liệu quá khứ “sạch”, khớp lệnh lý tưởng hơn và chi phí thường bị đánh giá thấp. Vì vậy cần tính đầy đủ các [chi\_phi\_giao\_dich](../concepts/chi_phi_giao_dich) và [truot\_gia](../concepts/truot_gia) để chiến lược còn lợi thế khi đưa vào giao dịch thật. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Các khoản chi phí như hoa hồng, spread, phí qua đêm, thuế, [trượt giá](../concepts/truot_gia)… trong backtest thường không giống môi trường thực. Trong đó [truot\_gia](../concepts/truot_gia) và [spread](../concepts/spread) khác biệt nhiều nhất. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

## Điểm cần chú ý

* Spread có thể giãn rộng ở thời điểm chuyển giao ngày mới, nhất là cặp ít thanh khoản. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)
* Trượt giá diễn ra ngẫu nhiên theo thời điểm; có lúc cực đoan. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)
* Với chiến lược giữ lệnh qua đêm (swing), cần tính swap và [gaap](../concepts/gaap) (khoảng trống giá) để tránh sai lệch khi [lệnh cắt lỗ](../concepts/lenh_cat_lo)/ chờ không khớp đúng mức đặt. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Backtest thường lạc quan vì dữ liệu quá khứ “sạch”, khớp lệnh lý tưởng và chi phí thường bị ước lượng thấp. Trong thực tế, độ trễ, thanh khoản và biến động trong lúc đặt lệnh có thể khiến kết quả lệch đáng kể so với mô phỏng.

Chênh lệch giữa backtest và thực thi thường đến từ dữ liệu không phản ánh đúng chi phí thực tế như trượt giá, phí giao dịch, funding/fee swap và độ trễ khớp lệnh. Nếu hệ thống không có lớp giám sát các chi phí thực thi theo thời gian thực, bạn sẽ chỉ thấy “kết quả xấu” mà không biết phần nào gây lệch. Vì vậy, chi phí thực tế nên được đưa vào vòng lặp vận hành để phát hiện sớm khi điều kiện thị trường thay đổi.

## Liên kết & Insight

Chi phí thực tế trong backtest nhắc rằng mô phỏng thường “đẹp” hơn giao dịch thật vì dữ liệu quá khứ sạch và khớp lệnh lý tưởng. Khi bạn đưa chiến lược ra thị trường, các khoản như [chi\_phi\_giao\_dich](../concepts/chi_phi_giao_dich) và đặc biệt là [truot\_gia](../concepts/truot_gia)/[spread](../concepts/spread) có thể ăn mòn lợi thế, làm kết quả lệch đáng kể. Insight cốt lõi là: muốn biết chiến lược có bền không, phải coi backtest chỉ là bản nháp và luôn tính đủ ma sát thực thi trước khi tin vào lợi nhuận.

## Liên quan

* [chi\_phi\_giao\_dich](../concepts/chi_phi_giao_dich)
* [truot\_gia](../concepts/truot_gia)
* [spread](../concepts/spread)
* swap
* [gaap](../concepts/gaap)