---
title: Đặt cược bất đối xứng
source_url: https://wiki.turtletrading.vn/concepts/dat_cuoc_bat_doi_xung
tags: []
backlinks: []
related_count: 6
crawled_at: '2026-04-21T05:00:09Z'
---

# Đặt cược bất đối xứng

Đặt cược bất đối xứng là nguyên lý thiết kế chiến lược: khi sai thì mất ít, còn khi đúng thì ăn nhiều. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Bài viết mô tả dấu hiệu vận hành qua quan hệ [equity\_balance](../concepts/equity_balance): Equity thường cao hơn Balance khi chiến lược giữ các lệnh đang chạy đúng và cắt bỏ nhanh phần đang thua. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Nguyên lý này liên quan đến việc tối ưu cấu trúc phần thưởng lệch phải (long convexity) để tận dụng [phan\_phoi\_duoi\_beo](../concepts/phan_phoi_duoi_beo): trong môi trường [đuôi béo](../concepts/duoi_beo), phần lớn kết quả dài hạn đến từ một số ít biến động cực lớn. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

## Liên kết & Insight

là nguyên lý thiết kế chiến lược nhằm tạo cấu trúc phần thưởng lệch phải: sai thì cắt sớm, đúng thì để chạy. Nó thường được kiểm chứng qua quan hệ [equity\_balance](../concepts/equity_balance)—khi vận hành đúng, Equity có xu hướng cao hơn Balance vì phần thua bị giới hạn còn phần thắng được tích lũy. Insight cốt lõi là lợi nhuận dài hạn không cần thắng nhiều, mà cần “đúng cấu trúc” để tận dụng đuôi rủi ro và đuôi cơ hội.

## Liên quan

* [equity\_balance](../concepts/equity_balance): Equity/Balance phản ánh cấu trúc “giữ đúng – cắt sai”.
* [duoi\_beo\_trong\_giao\_dich](../concepts/duoi_beo_trong_giao_dich): đuôi béo khiến bất đối xứng càng quan trọng.
* [tail\_risk](../concepts/tail_risk): bất đối xứng nhằm giảm [rủi ro đuôi trái](../concepts/rui_ro_duoi_trai).
* long convexity: khái niệm tương ứng với “mua độ lồi” trong bài.