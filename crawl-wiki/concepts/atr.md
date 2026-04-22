---
title: ATR
source_url: https://wiki.turtletrading.vn/concepts/atr
tags: []
backlinks: []
related_count: 8
crawled_at: '2026-04-21T04:59:50Z'
---

# ATR

ATR (Average True Range) là chỉ báo biến động được dùng để chuẩn hóa khoảng cách [dừng lỗ](../concepts/dung_lo). Trong chương này, ATR được dùng để đặt dừng lỗ ban đầu bằng 2,5 lần ATR và sau đó kiểm tra/ tối ưu tham số ATR trong một dải giá trị [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057). Việc dùng ATR giúp chiến lược có tham số phổ biến và có thể hoạt động ổn định trên một dải tham số rộng [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057).

ATR có thể được xem như một thước đo gián tiếp về mức độ “dễ dịch chuyển” của giá: khi thị trường đi qua các vùng [thanh khoản mỏng](../concepts/thanh_khoan_mong), biến động thường mở rộng và ATR có xu hướng tăng. Ngược lại, trong giai đoạn đi ngang với thanh khoản dày quanh vùng giá trị, biên dao động thường hẹp hơn nên ATR có thể giảm hoặc đi ngang.

[Dừng lỗ theo biến động](../concepts/dung_lo_theo_bien_dong) (thường đo bằng ATR) giúp điểm cắt lỗ “đủ rộng” để chịu nhiễu, đồng thời “đủ chặt” để không biến giao dịch thành một canh bạc. Khi dùng ATR theo tỷ lệ bội số, bạn chuẩn hóa được khoảng cách dừng lỗ giữa các tài sản và khung thời gian khác nhau, nên việc quản trị rủi ro trở nên nhanh và nhất quán. Điểm dừng theo biến động cũng khó bị đoán hơn so với các mức cố định, giảm khả năng bị thị trường quét.

ATR có thể được dùng như một thước đo biến động để đặt khoảng cách dừng lỗ theo “độ rộng” thực tế của giá, thay vì dùng một con số cố định. Khi dừng lỗ được đặt theo bội số ATR (ví dụ 2,5x), hệ thống sẽ tự thích nghi tương đối với giai đoạn biến động cao/thấp. Nhờ đó, [rủi ro trên mỗi lệnh](../concepts/rui_ro_tren_moi_lenh) có xu hướng ổn định hơn giữa các tài sản và giai đoạn khác nhau.

## Liên kết & Insight

ATR là cách chuẩn hóa biến động để chuyển ý tưởng quản trị rủi ro thành con số hành động, đặc biệt trong [dung\_lo\_theo\_bien\_dong](../concepts/dung_lo_theo_bien_dong). Khi ATR tăng, khoảng dao động “dễ mở rộng” hơn nên dừng lỗ cần đủ rộng để chịu nhiễu; khi ATR giảm, [thị trường đi ngang](../concepts/thi_truong_di_ngang) hơn nên khoảng dừng có thể gọn lại. Insight cốt lõi là: dùng ATR giúp dừng lỗ bớt cảm tính, khó bị thị trường quét hơn và giúp chiến lược nhất quán giữa các tài sản/khung thời gian.

## Liên quan

* [dung\_lo\_theo\_atr](../concepts/dung_lo_theo_atr)
* [quan\_ly\_rui\_ro](../concepts/quan_ly_rui_ro)
* [backtest](../concepts/backtest)