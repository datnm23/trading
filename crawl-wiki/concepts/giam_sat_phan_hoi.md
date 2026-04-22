---
title: Giám sát phản hồi
source_url: https://wiki.turtletrading.vn/concepts/giam_sat_phan_hoi
tags: []
backlinks: []
related_count: 4
crawled_at: '2026-04-21T05:00:23Z'
---

# Giám sát phản hồi

Giám sát phản hồi là lớp theo dõi hệ thống giao dịch khi chạy ngoài đời, giúp phát hiện bất thường và chẩn đoán lỗi. Lớp này theo dõi P/L, chi phí thực thi, [trượt giá](../concepts/truot_gia), funding, phí swap, trạng thái hoạt động của từng bộ phận và phát cảnh báo khi có điều gì đó bất thường. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Giám sát phản hồi biến hệ thống từ “chạy mù” thành cấu trúc có thể quan sát, chẩn đoán và cải tiến; nếu không có nó, ta chỉ nhìn thấy kết quả cuối cùng mà không hiểu nguyên nhân bên trong. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

## Liên kết & Insight

Giám sát phản hồi kết nối với [truot\_gia](../concepts/truot_gia) và [chi\_phi\_thuc\_te\_backtest](../concepts/chi_phi_thuc_te_backtest) để trả lời câu hỏi “thực thi có khác giả định không?”. Khi theo dõi P/L, chi phí, trượt giá, funding/fee và trạng thái hệ thống, bạn phát hiện sớm các lệch thường gặp thay vì chỉ nhìn kết quả cuối cùng. Insight chính là: một chiến lược chỉ thật sự đáng tin khi bạn quan sát được nguyên nhân bên trong, chứ không chỉ so sánh lợi nhuận.

## Liên quan

* [truot\_gia](../concepts/truot_gia): giám sát trượt giá để hiểu sai lệch thực thi.
* [chi\_phi\_thuc\_te\_backtest](../concepts/chi_phi_thuc_te_backtest): đối chiếu chi phí thực tế với giả định [backtest](../concepts/backtest).
* [repaint](../concepts/repaint): các vấn đề dữ liệu/tín hiệu có thể được phát hiện qua giám sát bất thường.