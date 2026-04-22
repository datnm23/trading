---
title: Lợi nhuận hằng năm / Mức sụt giảm tối đa
source_url: https://wiki.turtletrading.vn/concepts/annual_return_max_drawdown
tags: []
backlinks: []
related_count: 5
crawled_at: '2026-04-21T04:59:47Z'
---

# Lợi nhuận hằng năm / Mức sụt giảm tối đa

Annual Return/[Max Drawdown](../concepts/max_drawdown) là chỉ số so sánh lợi nhuận hàng năm với mức [max\_drawdown](../concepts/max_drawdown) tối đa, giúp đánh giá hiệu suất có tính đến cả rủi ro và thời gian [backtest](../concepts/backtest). [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Tác giả cho rằng đây là chỉ số quan trọng vì Recovery Factor (tỷ lệ lợi nhuận so với drawdown) không tính đến yếu tố thời gian, nên khó so sánh giữa các chiến lược có quãng [backtest](../concepts/backtest) khác nhau. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

## Cách dùng

* Có thể dùng để so sánh với mua và nắm giữ (ví dụ S&P 500) và xem chiến lược có “đánh bại thị trường” hay không. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)
* Tác giả nêu ngưỡng thực hành: cần ít nhất lớn hơn 0,5 (trong bối cảnh kiểm tra dài hạn, ví dụ ≥15 năm). [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Chỉ số so sánh lợi nhuận hàng năm với [max\_drawdown](../concepts/max_drawdown) giúp bạn nhìn hiệu suất theo hướng “đổi rủi ro lấy lợi nhuận”, thay vì chỉ nhìn mức tăng. Một chiến lược có thể có annual return cao nhưng drawdown quá lớn sẽ làm bạn khó tồn tại đủ lâu để EV phát huy.

Chỉ số Annual Return/Max Drawdown có thể được dùng để so sánh hiệu quả theo hướng “lợi nhuận tương ứng với mức chịu đựng rủi ro tối đa”. Trong trường hợp hệ thống theo xu hướng thuần túy, nếu chỉ số này vượt trội so với một benchmark như S&P 500, nó gợi ý rằng lợi nhuận tạo ra không chỉ là [may mắn](../concepts/may_man) ngắn hạn. Tuy nhiên, vẫn cần kiểm tra thêm [phân phối lợi nhuận](../concepts/phan_phoi_loi_nhuan) và độ ổn định tham số để củng cố kết luận.

Chỉ nhìn annual return dễ dẫn tới ảo giác về độ bền của chiến lược, vì lợi nhuận cao thường đi kèm những giai đoạn sụt giảm khó chịu. Thực tế, điều quan trọng là mối quan hệ giữa lợi nhuận kỳ vọng và mức drawdown tối đa mà bạn có thể chịu được mà không phá vỡ kỷ luật. Một hệ thống “không chết” trong các chu kỳ xấu thường đáng giá hơn hệ thống có lợi nhuận đẹp nhưng dễ cháy.

## Liên kết & Insight

Annual Return/Max Drawdown là cách quy đổi hiệu suất theo hướng “lợi nhuận so với mức chịu đựng rủi ro tối đa”, giúp bạn không bị đánh lừa bởi chỉ nhìn tăng trưởng. Nó gắn trực tiếp với [max\_drawdown](../concepts/max_drawdown) và nhắc rằng thời gian phục hồi cũng quan trọng, nên cần đặt trong bối cảnh [backtest](../concepts/backtest) đủ dài để đánh giá độ bền. Khi chỉ số này cao, chiến lược có xu hướng tạo lợi nhuận mà không khiến bạn bị “đánh gục” quá sớm, tăng xác suất tồn tại để lợi thế phát huy. Insight cốt lõi là tối ưu không chỉ để thắng, mà để thắng theo cách bạn vẫn còn đủ vốn và kỷ luật khi thị trường đảo chiều.

## Liên quan

* [max\_drawdown](../concepts/max_drawdown)
* [drawdown](../concepts/drawdown)
* recovery factor