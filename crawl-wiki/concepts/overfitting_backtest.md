---
title: Quá khớp backtest
source_url: https://wiki.turtletrading.vn/concepts/overfitting_backtest
tags: []
backlinks: []
related_count: 4
crawled_at: '2026-04-21T05:00:56Z'
---

# Quá khớp backtest

Quá khớp (overfitting) xảy ra khi chiến lược được điều chỉnh để tối ưu kết quả [backtest](../concepts/backtest) tốt nhất, nhưng giá trị kỳ vọng thực sự thấp hơn. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Quá khớp có thể biểu hiện khi chiến lược chỉ phù hợp với một kịch bản tốt nhất đã xảy ra trong quá khứ, và khi áp dụng thực tế thì hiệu suất “hồi quy về giá trị thực”. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

## Dấu hiệu và cơ chế

* Kết quả backtest quá nhạy với thay đổi tham số nhỏ (ví dụ EMA 30 vs EMA 31 cho lợi nhuận khác biệt lớn). [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)
* Tối ưu hóa tham số có thể tạo ra vùng tham số “đỉnh nhọn” thay vì vùng ổn định. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

## Liên kết & Insight

Quá khớp backtest là việc bạn chỉnh chiến lược để tối ưu kết quả trên [backtest](../concepts/backtest) tốt nhất, nhưng kỳ vọng thực ngoài mẫu lại thấp hơn. Dấu hiệu hay gặp là hiệu suất nhạy bất thường với thay đổi nhỏ của tham số, tạo ra “đỉnh nhọn” thay vì vùng ổn định—một kiểu bẫy tâm lý rằng tín hiệu chắc chắn hơn thực tế. Insight là hãy xem backtest như bài kiểm tra độ bền: nếu chiến lược chỉ sống nhờ một kịch bản quá cụ thể, nó sẽ “hồi quy về giá trị thực” khi gặp dữ liệu mới, và bạn cần các cách kiểm tra như [monte\_carlo](../concepts/monte_carlo) hoặc tư duy chống tối ưu quá tay.

## Liên quan

* [con\_khi\_may\_danh\_chu](../concepts/con_khi_may_danh_chu)
* [monte\_carlo](../concepts/monte_carlo)
* [lui\_duoi\_phai](../concepts/lui_duoi_phai)
* lưoi dao occam