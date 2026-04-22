---
title: Repaint
source_url: https://wiki.turtletrading.vn/concepts/repaint
tags: []
backlinks: []
related_count: 4
crawled_at: '2026-04-21T05:01:06Z'
---

# Repaint

Repaint là hiện tượng tín hiệu trong quá khứ bị thay đổi khi dữ liệu mới xuất hiện, khiến [backtest](../concepts/backtest) có thể “đẹp giả tạo” dù chiến lược thực tế không thể giao dịch như vậy. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Repaint thường đi kèm với các lỗi khác như [look\_ahead\_bias](../concepts/look_ahead_bias) (dùng thông tin chưa tồn tại) và làm tăng nguy cơ [duoi\_bat\_dinh](../concepts/duoi_bat_dinh)/ảo giác về lợi thế. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

## Dấu hiệu và cách phòng

* Đảm bảo mọi tín hiệu chỉ được tạo từ dữ liệu đã tồn tại đúng thời điểm ra quyết định. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)
* Tránh các chỉ báo/tín hiệu có tính chất vẽ lại. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

## Liên kết & Insight

Repaint là lỗi/hiện tượng khiến tín hiệu trong quá khứ bị thay đổi khi dữ liệu mới xuất hiện, làm [backtest](../concepts/backtest) có thể trông “đẹp” dù ngoài thực tế bạn không thể giao dịch như vậy. Nó thường đi chung với [look\_ahead\_bias](../concepts/look_ahead_bias) vì cùng một cơ chế là vô tình dùng thông tin chưa tồn tại tại thời điểm ra quyết định. Khi [backtest](../concepts/backtest) bị thổi phồng, bạn dễ rơi vào ảo giác lợi thế và sau đó bị đuối trong thị trường thật. Insight cốt lõi: muốn đánh giá chiến lược nghiêm túc, bạn phải kiểm tra tín hiệu có “vẽ lại” không và ưu tiên quy trình cho kết quả có thể tái lập, tức hướng tới [backtest\_chinh\_xac](../concepts/backtest_chinh_xac).

## Liên quan

* [look\_ahead\_bias](../concepts/look_ahead_bias)
* [backtest\_chinh\_xac](../concepts/backtest_chinh_xac)
* [duoi\_bat\_dinh](../concepts/duoi_bat_dinh)