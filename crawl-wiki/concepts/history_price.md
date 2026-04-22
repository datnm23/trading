---
title: Giá lịch sử
source_url: https://wiki.turtletrading.vn/concepts/history_price
tags: []
backlinks: []
related_count: 5
crawled_at: '2026-04-21T05:00:28Z'
---

# Giá lịch sử

History price là quá khứ của giá, được dùng để giải thích rằng giá tương lai chịu ảnh hưởng bởi chính lịch sử của nó (xu hướng, động lượng, mẫu hình để lại “dấu vết”) [📄 Nguồn](https://www.turtletrading.vn/2025/08/tai-sao-du-oan-gia-thi-truong-lai-kho.html).

Trong mô hình, thành phần này tương tác với [order\_flow](../concepts/order_flow) và [macro](../concepts/macro) qua hàm tương tác phi tuyến [phi\_tuyen\_gia](../concepts/phi_tuyen_gia) [📄 Nguồn](https://www.turtletrading.vn/2025/08/tai-sao-du-oan-gia-thi-truong-lai-kho.html). Vì vậy, các giả định “bất biến” về quan hệ quá khứ–tương lai có thể sai khi hành vi đám đông thay đổi [📄 Nguồn](https://www.turtletrading.vn/2025/08/tai-sao-du-oan-gia-thi-truong-lai-kho.html).

## Liên kết & Insight

liên kết với [order\_flow](../concepts/order_flow) và [macro](../concepts/macro) vì quá khứ của giá không chỉ là “dữ liệu cũ”, mà là dấu vết hành vi có thể tương tác với dòng lệnh và bối cảnh kinh tế. Khi đưa vào mô hình phi tuyến như [phi\_tuyen\_gia](../concepts/phi_tuyen_gia), các mẫu lịch sử có thể mất ý nghĩa nếu cách đám đông phản ứng thay đổi. Insight chính là đừng coi quá khứ như định luật: nó hữu ích để gợi ý, nhưng phải luôn kiểm tra lại vì quan hệ quá khứ–tương lai không bất biến.

## Liên quan

* phan tich ky thuat: lãnh địa của phân tích kỹ thuật dựa trên dấu vết quá khứ.
* [phi\_tuyen\_gia](../concepts/phi_tuyen_gia): tương tác phi tuyến khiến mẫu hình lịch sử có thể mất ý nghĩa.
* [qua\_khu\_se\_lap\_lai](../concepts/qua_khu_se_lap_lai): đối lập với giả định quá khứ lặp lại.
* [khong\_co\_he\_thong\_hoan\_hao](../concepts/khong_co_he_thong_hoan_hao): quan hệ không bất biến làm hệ thống khó “chắc chắn tuyệt đối”.