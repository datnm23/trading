---
title: Bot không thay cảm xúc
source_url: https://wiki.turtletrading.vn/concepts/bot_khong_thay_cam_xuc
tags: []
backlinks: []
related_count: 6
crawled_at: '2026-04-21T04:59:56Z'
---

# Bot không thay cảm xúc

Bot không loại bỏ cảm xúc con người; nó chỉ “dịch chuyển” cảm xúc đó lên tầng khác: bot được viết bởi quant và chịu quyết định của con người (hoảng khi [drawdown](../concepts/drawdown), tham khi lời, nhà quản lý gọi giảm vị thế, nhà đầu tư rút vốn khiến bot đóng lệnh…) [📄 Nguồn](https://www.turtletrading.vn/2026/04/ai-co-giet-thi-truong-khong.html). Vì vậy, giả định “bot = hệ thống không cảm xúc” là sai; cảm xúc vẫn tồn tại trong cơ chế vận hành và ra quyết định [📄 Nguồn](https://www.turtletrading.vn/2026/04/ai-co-giet-thi-truong-khong.html).

## Liên kết

* Gắn với [ao\_tuong\_kiem\_soat](../concepts/ao_tuong_kiem_soat) và [tam\_ly\_trading](../concepts/tam_ly_trading): con người vẫn là nguồn kích hoạt hành vi.
* Cơ chế stop/loss/margin call của bot liên quan tới [vong\_phan\_hoi\_phi\_tuyen](../concepts/vong_phan_hoi_phi_tuyen) và [tail\_risk](../concepts/tail_risk).
* Khi hệ thống vận hành sai kỳ vọng, trader dễ rơi vào [vong\_lap\_thay\_doi\_chien\_luoc](../concepts/vong_lap_thay_doi_chien_luoc).

## Liên kết & Insight

Bot không thay cảm xúc theo kiểu con người, nhưng nó không hề “vô cảm” trong nghĩa vận hành: cảm xúc được chuyển thành các ngưỡng và hành vi do con người thiết kế và kích hoạt. Khi drawdown làm người vận hành hoảng, hoặc khi lời khiến họ tham, bot vẫn có thể bị đổi tham số, giảm vị thế, hoặc bị đóng lệnh bởi cơ chế quản trị. Insight cốt lõi là coi bot như một hệ thống ra quyết định có người đứng sau, nên hãy nhìn vào [ao\_tuong\_kiem\_soat](../concepts/ao_tuong_kiem_soat) và các điểm kích hoạt phản hồi thay vì tin rằng bot tự động loại bỏ sai lầm.