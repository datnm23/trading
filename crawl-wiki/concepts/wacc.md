---
title: WACC
source_url: https://wiki.turtletrading.vn/concepts/wacc
tags: []
backlinks: []
related_count: 3
crawled_at: '2026-04-21T05:01:35Z'
---

# WACC

WACC (Chi phí vốn bình quân gia quyền) là tỷ suất chiết khấu thường dùng trong DCF để phản ánh chi phí vốn của doanh nghiệp [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057).

Tác giả nêu rằng r trong công thức DCF thường được lấy bằng WACC; r phụ thuộc doanh nghiệp/ngành và yếu tố thị trường, và có thể dao động theo mức độ trưởng thành/rủi ro [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057). Đồng thời, nếu tăng r thì [giá trị nội tại](../concepts/gia_tri_noi_tai) tính ra sẽ thấp hơn, giúp kỳ vọng lợi nhuận theo mức chiết khấu [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057).

## Liên kết & Insight

WACC là biến then chốt trong [dinh\_gia\_dcf](../concepts/dinh_gia_dcf) vì nó quyết định tỷ suất chiết khấu r dùng để quy đổi dòng tiền tương lai về hiện tại. Khi bạn ước lượng WACC cao hơn, giá trị nội tại thường giảm, nên WACC liên kết trực tiếp với mức “đắt/rẻ” trong mô hình. Insight cốt lõi là: thay vì tìm một con số r “đúng”, hãy dùng [bien\_an\_toan](../concepts/bien_an_toan) để chịu được sai số đầu vào, vì DCF nhạy với r và sai một chút có thể làm lệch toàn bộ kết luận.

## Liên quan

* [dinh\_gia\_dcf](../concepts/dinh_gia_dcf): WACC là đầu vào quan trọng.
* [gia\_tri\_noi\_tai](../concepts/gia_tri_noi_tai): giá trị nội tại nhạy với r.
* [bien\_an\_toan](../concepts/bien_an_toan): [biên an toàn](../concepts/bien_an_toan) giúp giảm rủi ro khi ước lượng đầu vào sai.