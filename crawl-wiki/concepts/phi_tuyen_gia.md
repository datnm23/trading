---
title: Phi tuyến giá
source_url: https://wiki.turtletrading.vn/concepts/phi_tuyen_gia
tags: []
backlinks: []
related_count: 6
crawled_at: '2026-04-21T05:01:00Z'
---

# Phi tuyến giá

Phi tuyến giá là đặc tính khi giá trong tương lai không chỉ phụ thuộc vào từng yếu tố riêng lẻ mà còn phụ thuộc vào **tương tác** giữa các yếu tố đó; vì vậy một thay đổi nhỏ ở một thành phần có thể làm kết quả đổi hướng hoàn toàn [📄 Nguồn](https://www.turtletrading.vn/2025/08/tai-sao-du-oan-gia-thi-truong-lai-kho.html).

Trong mô hình được nêu, giá tương lai được viết như một hàm hợp phức tạp, trong đó có thành phần tương tác phi tuyến [tu\_tham\_chieu](../concepts/tu_tham_chieu) và các thành phần như [order\_flow](../concepts/order_flow)/[macro](../concepts/macro) không độc lập [📄 Nguồn](https://www.turtletrading.vn/2025/08/tai-sao-du-oan-gia-thi-truong-lai-kho.html).

## Liên kết & Insight

Phi tuyến giá nhắc rằng giá tương lai không chỉ là tổng của từng yếu tố rời rạc, mà là kết quả của tương tác giữa chúng, nên một thay đổi nhỏ cũng có thể đảo hướng cả kịch bản. Vì các thành phần như [order flow](../concepts/order_flow) và macro không độc lập, dự báo dễ bị “tác động ngược” khi hành vi thị trường phản hồi lại mô hình. Insight cốt lõi là đừng tối ưu theo giả định mọi thứ cộng tuyến tính; hãy coi [tu\_tham\_chieu](../concepts/tu_tham_chieu) và [nhieu\_thi\_truong](../concepts/nhieu_thi_truong) là lý do khiến sai số nhỏ có thể khuếch đại, đặc biệt khi dùng [khung\_thoi\_gian\_nho](../concepts/khung_thoi_gian_nho).

## Liên quan

* [tu\_tham\_chieu](../concepts/tu_tham_chieu): mô hình có thể bị “tác động ngược” từ hành vi/đầu vào.
* [nhieu\_thi\_truong](../concepts/nhieu_thi_truong): phi tuyến khiến nhiễu nhỏ vẫn có thể khuếch đại thành sai lệch lớn.
* [thi\_truong\_khong\_du\_doan\_het](../concepts/thi_truong_khong_du_doan_het): phi tuyến là một lý do khiến dự đoán khó trọn vẹn.
* [khung\_thoi\_gian\_nho](../concepts/khung_thoi_gian_nho): timeframe nhỏ thường làm tương tác phi tuyến mạnh hơn.