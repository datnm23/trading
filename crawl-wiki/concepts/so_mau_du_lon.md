---
title: Số mẫu đủ lớn
source_url: https://wiki.turtletrading.vn/concepts/so_mau_du_lon
tags: []
backlinks: []
related_count: 5
crawled_at: '2026-04-21T05:01:11Z'
---

# Số mẫu đủ lớn

[Backtest](../concepts/backtest) cần được kiểm tra với số mẫu đủ lớn; một hệ thống chỉ được kiểm tra trong vài năm thường không có ý nghĩa vì chưa chứng minh hiệu suất qua nhiều giai đoạn thị trường. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Tác giả gợi ý chiến lược nên được kiểm tra ít nhất khoảng 10 năm và/hoặc số lượng lệnh lớn (từ vài chục nghìn đến hàng chục/hàng trăm nghìn lệnh) để giảm tác động của ngẫu nhiên. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

## Vì sao số mẫu lớn quan trọng

* Tỷ lệ thắng và [ty\_le\_thang\_va\_rr](../concepts/ty_le_thang_va_rr) là các tham số ước lượng từ dữ liệu; nếu số lệnh ít, các ước lượng dễ sai lệch so với giá trị thực. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)
* Khi số lệnh tăng, biên dao động của “khả năng” (likelihood) quanh giá trị thực sẽ thu hẹp, tăng độ chắc chắn. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

## Liên kết & Insight

Số mẫu đủ lớn nhắc rằng [backtest](../concepts/backtest) chỉ đáng tin khi được thử qua nhiều giai đoạn và đủ nhiều lệnh, vì các tham số như tỷ lệ thắng hay RR là ước lượng từ dữ liệu. Nếu chỉ chạy vài năm hoặc vài chục lệnh, kết quả dễ bị ngẫu nhiên dẫn dắt và không phản ánh khả năng thật. Insight cốt lõi là: tăng cỡ dữ liệu giúp biên dao động quanh “giá trị thực” thu hẹp, nên bạn nên kiểm tra chiến lược với ít nhất khoảng 10 năm hoặc hàng chục nghìn lệnh để giảm ảo tưởng từ [may mắn](../concepts/may_man).

## Liên quan

* [backtest](../concepts/backtest)
* [so\_mau\_du\_lon](../concepts/so_mau_du_lon)
* [phan\_phoi\_ngau\_nhien](../concepts/phan_phoi_ngau_nhien)
* [luat\_so\_lon](../concepts/luat_so_lon)