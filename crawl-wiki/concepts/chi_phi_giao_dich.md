---
title: Chi phí giao dịch
source_url: https://wiki.turtletrading.vn/concepts/chi_phi_giao_dich
tags: []
backlinks: []
related_count: 7
crawled_at: '2026-04-21T05:00:00Z'
---

# Chi phí giao dịch

Chi phí giao dịch là các khoản phí/hao hụt phát sinh khi thực hiện giao dịch (ví dụ chênh lệch giá, hoa hồng, và các chi phí liên quan). [📄 Nguồn](https://www.turtletrading.vn/2024/12/thi-truong-tai-chinh-co-phai-la-mot-tro.html)

Trong bài viết, chi phí giao dịch được xem là yếu tố làm giảm tổng giá trị lợi nhuận trong các trò chơi gần [zero-sum](../concepts/zero_sum) ở ngắn hạn, khiến tổng lợi nhuận có thể nhỏ hơn 0. [📄 Nguồn](https://www.turtletrading.vn/2024/12/thi-truong-tai-chinh-co-phai-la-mot-tro.html)

Trong nhiều chiến lược, lợi thế có thể chỉ nhỉnh hơn mức hòa vốn một chút, nên chi phí giao dịch trở thành “khoảng đệm” quyết định bạn có còn EV dương hay không. Vì vậy, khi đánh giá hiệu suất, cần tính cả [spread](../concepts/spread), hoa hồng và các hao hụt thực thi khác chứ không chỉ nhìn lợi nhuận lý thuyết.

Chi phí giao dịch và [trượt giá](../concepts/truot_gia) là dạng “ma sát” làm mòn lợi thế, đặc biệt rõ khi bạn giao dịch trên [khung thời gian nhỏ](../concepts/khung_thoi_gian_nho). Một chiến lược có tỷ lệ R:R đẹp trên [backtest](../concepts/backtest) hình ảnh có thể trở thành [kỳ vọng âm](../concepts/ky_vong_am) khi đưa vào thực thi thực tế do giá khớp lệch khỏi giá dự kiến. Vì vậy, cần đưa chi phí và trượt giá vào đánh giá hiệu suất thay vì chỉ nhìn lợi nhuận danh nghĩa.

Chi phí giao dịch trong [backtest](../concepts/backtest) nên được đưa vào một cách thận trọng vì nó có thể bào mòn lợi thế, đặc biệt với chiến lược có số lượng lệnh lớn. Nếu thực tế có chiết khấu hoặc ưu đãi, vẫn nên chạy kịch bản với chi phí cao hơn để phòng sai lệch mô hình và điều kiện thị trường xấu hơn. Cách làm này giúp kết quả ít phụ thuộc vào giả định quá lạc quan.

Chi phí giao dịch không chỉ nằm ở commission mà còn gồm spread, trượt giá và các “ma sát” khi thị trường biến động mạnh. Với các mô hình thử thách hoặc cấp vốn, chỉ cần chi phí tăng nhẹ cũng có thể làm chiến lược vốn mỏng trở nên không còn lợi thế.

Trên [khung thời gian nhỏ](../concepts/khung_thoi_gian_nho), tổng chi phí giao dịch (spread, commission, trượt giá) có thể trở thành phần “ăn mòn” lợi nhuận kỳ vọng. Vì số lệnh nhiều, chỉ cần hiệu suất R:R bị suy giảm nhẹ cũng đủ làm chiến lược từ [kỳ vọng dương](../concepts/ky_vong_duong) chuyển sang [kỳ vọng âm](../concepts/ky_vong_am).

## Liên kết & Insight

Chi phí giao dịch là lớp ma sát làm giảm lợi nhuận ròng khi bạn chuyển từ mô hình sang thực thi, nên nó luôn phải được xem cùng với [truot\_gia](../concepts/truot_gia) và các giả định trong [backtest](../concepts/backtest). Khi chiến lược chỉ nhỉnh hơn mức hòa vốn, phí và độ lệch khớp lệnh có thể đẩy kỳ vọng từ dương sang âm, khiến kết quả trông “đẹp trên giấy” nhưng lại kém ngoài đời. Insight chính là: đánh giá hiệu suất phải tính cả spread, hoa hồng và hao hụt thực thi, vì đó mới là thứ quyết định EV của bạn.

## Liên quan

* [zero\_sum](../concepts/zero_sum)
* [zero\_sum](../concepts/zero_sum)
* [truot\_gia](../concepts/truot_gia)