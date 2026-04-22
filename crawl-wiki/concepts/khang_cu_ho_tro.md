---
title: Kháng cự và hỗ trợ
source_url: https://wiki.turtletrading.vn/concepts/khang_cu_ho_tro
tags: []
backlinks: []
related_count: 4
crawled_at: '2026-04-21T05:00:31Z'
---

# Kháng cự và hỗ trợ

Kháng cự và hỗ trợ là các mức giá ngang được dùng để phân loại trạng thái thị trường trong công cụ tự động: kháng cự được xác định bằng mức giá buôn cuối cùng cao nhất hoặc điểm xoay chuyển đổi xu hướng; hỗ trợ được xác định bằng mức giá buôn cuối cùng thấp nhất hoặc điểm xoay chuyển đổi xu hướng [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057). Khi giá nằm trên kháng cự thì coi là xu hướng tăng; khi giá nằm dưới hỗ trợ thì coi là xu hướng giảm; còn lại là đi ngang [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057).

## Liên kết & Insight

đóng vai trò như “bản đồ trạng thái” để phân loại thị trường trong các hệ thống [giao dịch tự động](../concepts/giao_dich_tu_dong): giá nằm trên vùng kháng cự thường được hiểu là xu hướng tăng, dưới hỗ trợ là xu hướng giảm, còn giữa hai vùng thì coi là đi ngang. Nó thường được kết hợp với [ema\_100](../concepts/ema_100) để lọc xu hướng và với [trend\_detector](../concepts/trend_detector) để xác định pha hiện tại, giúp giảm việc ra quyết định chỉ dựa vào cảm giác. Insight cốt lõi là: nếu không định nghĩa rõ vùng hành vi giá, chiến lược sẽ phản ứng trễ và dễ nhầm pha.

## Liên quan

* [ema\_100](../concepts/ema_100)
* [trend\_detector](../concepts/trend_detector)
* [pha\_vo\_kienh](../concepts/pha_vo_kienh)