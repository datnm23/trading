---
title: Tỷ lệ thắng và R:R
source_url: https://wiki.turtletrading.vn/concepts/ty_le_thang_va_rr
tags: []
backlinks: []
related_count: 7
crawled_at: '2026-04-21T05:01:31Z'
---

# Tỷ lệ thắng và R:R

Tỷ lệ thắng và R:R là hai thành phần cấu trúc phần thưởng quyết định [gia\_tri\_ky\_vong\_ev](../concepts/gia_tri_ky_vong_ev) của một chiến lược. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Bài viết nhấn mạnh trực giác thường sai: tỷ lệ thắng cao không đồng nghĩa có lợi nhuận, và tỷ lệ thắng thấp không đồng nghĩa không có lợi thế; điều quyết định là quan hệ giữa xác suất thắng, mức lời khi thắng và mức lỗ khi thua (tức cấu trúc R:R). [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

## Liên kết & Insight

Tỷ lệ thắng và R:R là “khung” quyết định [gia\_tri\_ky\_vong\_ev](../concepts/gia_tri_ky_vong_ev) của một chiến lược, vì lợi nhuận kỳ vọng không chỉ đến từ việc bạn thắng bao nhiêu lần mà còn từ việc mỗi lần thắng lời bao nhiêu và mỗi lần thua mất bao nhiêu. Khi chỉ nhìn tỷ lệ thắng cao, người ta dễ tự tin sai vì cấu trúc phần thưởng có thể khiến EV vẫn âm; ngược lại tỷ lệ thắng thấp vẫn có thể có lợi thế nếu R:R đủ tốt. Insight cốt lõi là hãy coi R:R như phần còn lại của xác suất thắng: muốn có lợi thế thì phải làm cho quan hệ “xác suất thắng × lời khi thắng” vượt “xác suất thua × lỗ khi thua”.

## Liên quan

* [gia\_tri\_ky\_vong\_ev](../concepts/gia_tri_ky_vong_ev): EV được tính từ [ty\_le\_thang](../concepts/ty_le_thang) và R:R.
* [loi\_the\_edge](../concepts/loi_the_edge): lợi thế nằm ở cấu trúc phần thưởng tạo EV dương.
* [duoi\_beo\_trong\_giao\_dich](../concepts/duoi_beo_trong_giao_dich): trong môi trường [đuôi béo](../concepts/duoi_beo), cấu trúc phần thưởng cần tránh [rủi ro đuôi](../concepts/tail_risk).
* [profit\_factor](../concepts/profit_factor): ngoài EV, Profit Factor cũng phản ánh lợi thế.