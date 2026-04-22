---
title: Taker
source_url: https://wiki.turtletrading.vn/concepts/taker
tags: []
backlinks: []
related_count: 3
crawled_at: '2026-04-21T05:01:14Z'
---

# Taker

Taker (nhà giao dịch chủ động) là người **lấy đi thanh khoản** bằng cách gửi lệnh thị trường để thực hiện ngay. Vì phải khớp ngay, taker sẽ lấy giá theo **bid tốt nhất** khi bán ngay và theo **ask tốt nhất** khi mua ngay [📄 Nguồn](https://www.turtletrading.vn/2025/01/tai-sao-gia-di-chuyen.html).

## Liên kết & Insight

Taker là người chủ động “lấy đi thanh khoản” bằng lệnh thị trường, nên giá thực hiện bị neo vào [gia\_bid\_ask](../concepts/gia_bid_ask) (bán thì ăn bid tốt nhất, mua thì ăn ask tốt nhất). Vì phải khớp ngay, taker thường tạo ra biến động theo tương tác lực mua/lực bán chủ động, gắn với [luc\_mua\_luc\_ban](../concepts/luc_mua_luc_ban). Insight cốt lõi là: bạn không chỉ giao dịch “ý tưởng”, mà còn giao dịch vào đúng mặt bằng thanh khoản—chi phí ẩn nằm ở việc bị kéo vào bid/ask ngay lập tức.

## Liên quan

* [gia\_bid\_ask](../concepts/gia_bid_ask): taker quyết định giá thực hiện ngay tại bid/ask tốt nhất.
* thanh khoan: taker “ăn” thanh khoản làm giá dễ di chuyển.
* [luc\_mua\_luc\_ban](../concepts/luc_mua_luc_ban): biến động xuất phát từ tương tác lực mua/lực bán chủ động.
* [maker](../concepts/maker): đối lập với taker (người cung cấp thanh khoản qua lệnh chờ).