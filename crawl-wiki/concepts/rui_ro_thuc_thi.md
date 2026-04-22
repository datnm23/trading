---
title: Rủi ro thực thi
source_url: https://wiki.turtletrading.vn/concepts/rui_ro_thuc_thi
tags: []
backlinks: []
related_count: 9
crawled_at: '2026-04-21T05:01:09Z'
---

# Rủi ro thực thi

Rủi ro thực thi là sự chênh lệch giữa giá dự kiến và giá thực tế nhận được khi vào lệnh, bao gồm [trượt giá](../concepts/truot_gia), giao dịch bị bỏ lỡ và các lỗi thực thi khác [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057).

Nhiều nội dung “đánh lừa” bằng [backtest](../concepts/backtest) chỉ nhìn trên biểu đồ với R:R đẹp nhưng bỏ qua trượt giá và chi phí; trên [khung thời gian nhỏ](../concepts/khung_thoi_gian_nho), chi phí/trượt giá càng làm suy yếu mạnh lợi thế, thậm chí biến chiến lược [kỳ vọng dương](../concepts/ky_vong_duong) thành [kỳ vọng âm](../concepts/ky_vong_am) [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057).

## Liên kết & Insight

Rủi ro thực thi liên kết chặt với [backtest](../concepts/backtest) vì nhiều [backtest](../concepts/backtest) chỉ cho kết quả “khớp giá đẹp” trên biểu đồ, trong khi thực tế luôn có sai lệch giữa giá dự kiến và giá nhận được. Nó cũng phụ thuộc vào [chi\_phi\_giao\_dich](../concepts/chi_phi_giao_dich) và [truot\_gia](../concepts/truot_gia), vì chi phí/trượt giá trên [khung thời gian nhỏ](../concepts/khung_thoi_gian_nho) có thể bào mòn lợi thế và làm chiến lược đổi chiều từ [kỳ vọng dương](../concepts/ky_vong_duong) sang [kỳ vọng âm](../concepts/ky_vong_am). Insight cốt lõi là: muốn biết chiến lược có sống được ngoài đời không, phải đánh giá hiệu suất sau khi trừ rủi ro thực thi, không chỉ nhìn lợi nhuận trên giấy.

## Liên quan

* [truot\_gia](../concepts/truot_gia): thành phần quan trọng của rủi ro thực thi.
* [chi\_phi\_giao\_dich](../concepts/chi_phi_giao_dich): chi phí làm giảm hiệu suất thực tế.
* [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam): backtest hình ảnh không phản ánh rủi ro thực thi.
* [chi\_phi\_giao\_dich\_an](../concepts/chi_phi_giao_dich_an): chi phí ẩn thường bị bỏ qua trong mô phỏng.

Rủi ro thực thi là chênh lệch giữa giá dự kiến và giá thực tế khi vào lệnh, bao gồm trượt giá, bỏ lỡ lệnh và lỗi vận hành. Nó làm suy yếu lợi thế vì backtest thường giả định khớp giá “lý tưởng” hoặc bỏ qua chi phí/độ trễ. Khi rủi ro thực thi lớn, một chiến lược có kỳ vọng dương trên giấy có thể trở thành kỳ vọng âm trong thực tế. Do đó cần đánh giá cùng [chi\_phi\_giao\_dich](../concepts/chi_phi_giao_dich) và [trượt\_giá](../trượt_giá) trước khi triển khai.