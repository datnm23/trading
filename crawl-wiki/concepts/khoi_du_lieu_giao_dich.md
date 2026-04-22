---
title: Khối dữ liệu giao dịch
source_url: https://wiki.turtletrading.vn/concepts/khoi_du_lieu_giao_dich
tags: []
backlinks: []
related_count: 1
crawled_at: '2026-04-21T05:00:31Z'
---

# Khối dữ liệu giao dịch

Khối dữ liệu giao dịch là phần thu thập, chuẩn hóa và làm sạch dữ liệu để toàn bộ hệ thống có thể “đọc cùng một ngôn ngữ”. Nó không tạo tín hiệu, mà đảm bảo dữ liệu cập nhật ổn định, nhất quán và phản ánh đúng điều kiện mà hệ thống sẽ gặp khi chạy thật. Nếu khối dữ liệu yếu, chiến lược có thể trông tốt trên [backtest](../concepts/backtest) nhưng thất bại khi triển khai. Khối này thường gắn chặt với các kiểm tra chất lượng dữ liệu và đồng bộ thời gian.

## Liên kết & Insight

Khối dữ liệu giao dịch liên kết với [backtest](../concepts/backtest) ở chỗ nó quyết định chiến lược “được đọc” như thế nào trước khi tạo ra kết quả. Nếu dữ liệu bị lệch giờ, thiếu sạch, hoặc không nhất quán, [backtest](../concepts/backtest) có thể cho ra tín hiệu đẹp nhưng triển khai sẽ lệch điều kiện thực. Insight cốt lõi là: dữ liệu không tạo lợi thế, nhưng dữ liệu kém có thể phá sạch lợi thế—vì vậy chất lượng và đồng bộ dữ liệu là nền tảng của mọi đánh giá.