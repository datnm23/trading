---
title: Trend following
source_url: https://wiki.turtletrading.vn/concepts/trend_following
tags: []
backlinks: []
related_count: 7
crawled_at: '2026-04-21T05:01:24Z'
---

# Trend following

Trend following là kiểu hệ thống giao dịch có cấu trúc payoff khác với mean reversion: thường có tỷ lệ thắng thấp hơn, thua lỗ nhỏ liên tục, nhưng lãi được để cho chạy không giới hạn. Bài viết dùng trend following như ví dụ về “cấu trúc của giàu có thực sự”: sai nhiều lần nhưng chỉ cần một con trend đủ lớn để trả lại tất cả [📄 Nguồn](https://www.turtletrading.vn/2026/02/cau-truc-thuc-su-cua-giau-co.html).

## Đặc trưng cấu trúc

* Lỗ được cắt sớm; lãi được để chạy, tạo ra bất đối xứng giữa đuôi trái và [đuôi phải](../concepts/duoi_phai) [📄 Nguồn](https://www.turtletrading.vn/2026/02/cau-truc-thuc-su-cua-giau-co.html).
* Trái với “tối ưu trung bình”, trend following nhắm vào hình dạng lệch phải của [phân phối lợi nhuận](../concepts/phan_phoi_loi_nhuan) [📄 Nguồn](https://www.turtletrading.vn/2026/02/cau-truc-thuc-su-cua-giau-co.html).

## Liên kết & Insight

kết nối với [trend\_detector](../concepts/trend_detector) ở chỗ: bộ lọc xu hướng giúp bạn chỉ “bật” chiến lược khi xác suất có trend đủ tốt, nhờ vậy giảm số lần thua liên tục. Về mặt cấu trúc, trend following thường chấp nhận thua nhỏ nhiều lần để đổi lấy khả năng hưởng lợi khi [đuôi phải](../concepts/duoi_phai) kéo dài, nên nó tương thích với tư duy [bat\_doi\_xung\_payoff](../concepts/bat_doi_xung_payoff) hơn là tối ưu trung bình. Insight cốt lõi là: bạn không cần đúng liên tục, bạn cần đúng đủ lớn—và đúng lớn thường đến từ việc để lãi chạy trong đúng bối cảnh.

## Liên quan

* [bat\_doi\_xung\_payoff](../concepts/bat_doi_xung_payoff)
* [phan\_phoi\_duoi\_beo](../concepts/phan_phoi_duoi_beo)
* [tail\_risk](../concepts/tail_risk)
* [grid\_mean\_reversion](../concepts/grid_mean_reversion)