---
title: Vòng phản hồi phi tuyến
source_url: https://wiki.turtletrading.vn/concepts/vong_phan_hoi_phi_tuyen
tags: []
backlinks: []
related_count: 6
crawled_at: '2026-04-21T05:01:34Z'
---

# Vòng phản hồi phi tuyến

Vòng phản hồi phi tuyến là cơ chế khiến biến động khuếch đại: khi giá giảm vì sợ hãi/hoảng loạn, người khác cũng sợ và bán tiếp, tạo vòng lặp làm sinh ra các trạng thái cực đoan và xu hướng [📄 Nguồn](https://www.turtletrading.vn/2026/04/ai-co-giet-thi-truong-khong.html). Tác giả nhấn mạnh trend và crash không đến từ “cảm xúc” đơn lẻ, mà đến từ vòng phản hồi cộng với hàm phản ứng phi tuyến (ví dụ stop loss, mức thanh lý, margin call, risk rebalancing) [📄 Nguồn](https://www.turtletrading.vn/2026/04/ai-co-giet-thi-truong-khong.html).

## Liên kết

* Liên quan tới [he\_phi\_tuyen](../concepts/he_phi_tuyen) và [thi\_truong\_ngau\_nhien\_khong\_the\_du\_doan\_het](../thi_truong_ngau_nhien_khong_the_du_doan_het).
* Khi vòng lặp kích hoạt các trạng thái cực đoan, nó liên quan tới [tail\_risk](../concepts/tail_risk) và [phan\_phoi\_duoi\_beo](../concepts/phan_phoi_duoi_beo).
* Trong trading, vòng phản hồi có thể làm bạn nhầm “mất lợi thế” khi thực ra chỉ là [drawdown\_keo\_dai](../concepts/drawdown_keo_dai).

## Liên kết & Insight

Vòng phản hồi phi tuyến giải thích vì sao thị trường có thể “tự đẩy” mình vào trạng thái cực đoan: một cú giảm kích hoạt các cơ chế phản ứng như stop loss, margin call và tái cân bằng rủi ro, rồi nỗi sợ lan thành bán tháo tiếp. Nó gắn chặt với [he\_phi\_tuyen](../concepts/he_phi_tuyen) và cách các cú sốc trong [thi\_truong\_ngau\_nhien\_khong\_the\_du\_doan\_het](../thi_truong_ngau_nhien_khong_the_du_doan_het) không chỉ là nhiễu ngẫu nhiên mà còn bị khuếch đại bởi phản ứng phi tuyến. Insight cốt lõi là đừng chỉ đổ lỗi cho “cảm xúc”; hãy xem các ngưỡng vận hành (liquidation, rebalancing) vì chúng thường là thứ tạo ra tail risk và làm [drawdown](../concepts/drawdown) kéo dài hơn bạn tưởng.