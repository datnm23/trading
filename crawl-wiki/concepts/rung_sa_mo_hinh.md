---
title: Bản đồ trên sa mạc
source_url: https://wiki.turtletrading.vn/concepts/rung_sa_mo_hinh
tags: []
backlinks: []
related_count: 2
crawled_at: '2026-04-21T05:01:09Z'
---

# Bản đồ trên sa mạc

“Bản đồ trên sa mạc” là cách mô tả việc dùng mô hình thống kê như một bản đồ để lái xe trong điều kiện thực tế không giống giả định. Nếu mô hình dựa trên [gaussian\_assumption](../concepts/gaussian_assumption) hoặc ước lượng mean/variance không ổn định, thì bản đồ sẽ sai đúng lúc cần nhất. Khi đó, quản trị rủi ro và thiết kế chiến lược phải ưu tiên khả năng chịu đuôi rủi ro thay vì chỉ tối ưu theo kỳ vọng.

## Liên kết & Insight

“Bản đồ trên sa mạc” nhắc rằng mô hình thống kê chỉ là bản đồ, còn thực tế là sa mạc—khác giả định thì sai số sẽ lộ ra đúng lúc bạn cần nhất. Nó liên kết với [gaussian\_assumption](../concepts/gaussian_assumption) vì khi bạn dựa quá nhiều vào giả định phân phối (hoặc mean/variance không ổn định), bạn dễ đánh giá thấp [rủi ro đuôi](../concepts/tail_risk). Insight cốt lõi là quản trị rủi ro và thiết kế chiến lược phải ưu tiên khả năng chịu “đuôi xấu” thay vì chỉ tối ưu kỳ vọng, tức là coi trọng cách mô hình có thể sai khi điều kiện đổi.