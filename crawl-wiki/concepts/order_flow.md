---
title: Order flow
source_url: https://wiki.turtletrading.vn/concepts/order_flow
tags: []
backlinks: []
related_count: 4
crawled_at: '2026-04-21T05:00:55Z'
---

# Order flow

Order flow là dòng lệnh/biểu hiện hành vi giao dịch thể hiện qua các chỉ báo như bid/ask delta, open interest, funding và các cụm thanh khoản; nó được mô tả như một “nhịp tim” tác động ngược lên giá [📄 Nguồn](https://www.turtletrading.vn/2025/08/tai-sao-du-oan-gia-thi-truong-lai-kho.html).

Bài viết nhấn mạnh order flow không đứng riêng mà tương tác với [history\_price](../concepts/history_price) và [macro](../concepts/macro) theo cơ chế phi tuyến [phi\_tuyen\_gia](../concepts/phi_tuyen_gia) [📄 Nguồn](https://www.turtletrading.vn/2025/08/tai-sao-du-oan-gia-thi-truong-lai-kho.html). Ở timeframe nhỏ, order flow biến thiên mạnh do bot/HFT/stop/order ảo, khiến việc đo đạc dễ làm “phá hỏng” chính order flow [📄 Nguồn](https://www.turtletrading.vn/2025/08/tai-sao-du-oan-gia-thi-truong-lai-kho.html).

## Liên kết & Insight

mô tả “nhịp tim” của thị trường qua dòng lệnh và các tín hiệu như bid/ask delta, open interest, funding, thanh khoản—nó tác động ngược lên giá theo kiểu phi tuyến. Vì vậy, khi đọc order flow cần đặt nó trong bối cảnh [history\_price](../concepts/history_price) và [macro](../concepts/macro) để hiểu vì sao cùng một tín hiệu lại dẫn tới kết quả khác nhau. Insight cốt lõi là: ở [khung\_thoi\_gian\_nho](../concepts/khung_thoi_gian_nho), nhiễu từ bot/HFT/stop/order ảo làm order flow biến động mạnh, khiến việc đo đạc dễ “phá hỏng” chính thứ bạn đang cố khai thác.

## Liên quan

* [history\_price](../concepts/history_price): quá khứ để lại dấu vết ảnh hưởng đến bước tiếp theo.
* [phi\_tuyen\_gia](../concepts/phi_tuyen_gia): tương tác giữa các thành phần làm kết quả nhạy cảm.
* [khung\_thoi\_gian\_nho](../concepts/khung_thoi_gian_nho): timeframe nhỏ khiến order flow chi phối mạnh.
* market maker: sân chơi order flow thường nghiêng về market maker/bot.