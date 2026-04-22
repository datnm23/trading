---
title: Quản lý drawdown
source_url: https://wiki.turtletrading.vn/concepts/quan_ly_drawdown
tags: []
backlinks: []
related_count: 8
crawled_at: '2026-04-21T05:01:02Z'
---

# Quản lý drawdown

Quản lý drawdown là cách giữ mức sụt giảm vốn trong “vùng cho phép” để người giao dịch đủ vững tâm lý tiếp tục duy trì chiến lược. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)

## Cách tiếp cận

* Dùng [dung\_lo](../concepts/dung_lo) và điều chỉnh khối lượng giao dịch để kiểm soát drawdown. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)
* Với chiến lược không đặt cắt lỗ như [dca](../concepts/dca) hoặc [martingale](../concepts/martingale) ([quản lý vốn](../concepts/quan_ly_von) [martingale](../concepts/martingale)), khó kiểm soát rủi ro tối đa vì có thể “gồng lỗ đến vô cực”, nên không đo lường được drawdown tối đa. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)
* Xác định mức rủi ro phù hợp bằng mô phỏng [monte\_carlo](../concepts/monte_carlo) dựa trên hiệu suất quá khứ. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)

## Liên kết & Insight

Quản lý drawdown là cách biến biến động lợi nhuận thành một “giới hạn tâm lý” để bạn không bị cuốn khỏi chiến lược khi vốn sụt. Nó gắn chặt với [dung\_lo](../concepts/dung_lo) vì drawdown chỉ thực sự có ý nghĩa khi bạn biết mức nào là còn chịu được, và khi cần thì điều chỉnh khối lượng để giữ rủi ro trong vùng cho phép. Với các chiến lược không có cắt lỗ như [dca](../concepts/dca), bạn dễ rơi vào tình trạng không đo được drawdown tối đa, nên insight quan trọng là phải dùng mô phỏng như [monte\_carlo](../concepts/monte_carlo) để ước lượng kịch bản xấu dựa trên dữ liệu quá khứ.

## Liên quan

* [drawdown](../concepts/drawdown): đại lượng cần được giữ trong ngưỡng cho phép. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)
* [quan\_ly\_rui\_ro](../concepts/quan_ly_rui_ro): khung quản trị rủi ro tổng thể để tránh “phá sản do vận đen”. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)
* [risk\_of\_ruin](../concepts/risk_of_ruin): mục tiêu thực tế là giảm khả năng rơi vào kịch bản xấu nhất. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)