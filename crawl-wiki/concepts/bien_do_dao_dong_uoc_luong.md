---
title: Biên độ dao động ước lượng
source_url: https://wiki.turtletrading.vn/concepts/bien_do_dao_dong_uoc_luong
tags: []
backlinks: []
related_count: 7
crawled_at: '2026-04-21T04:59:53Z'
---

# Biên độ dao động ước lượng

Biên độ dao động của một chỉ số (ở đây là [tỉ lệ thắng](../concepts/ty_le_thang)) phản ánh khoảng giá trị mà “[tỉ lệ thắng](../concepts/ty_le_thang) thực tế” có thể rơi vào với một mức xác suất nhất định. Khi số lệnh [backtest](../concepts/backtest) tăng, biên độ này thu hẹp, làm tăng mức độ chắc chắn mà ta rút ra từ kết quả kiểm tra. [📄 Nguồn](https://www.turtletrading.vn/2025/11/giai-quyet-nan-e-quy-nap-o-chac-chan.html)

Nếu số lệnh trong [backtest](../concepts/backtest) ít, các ước lượng như tỷ lệ thắng và tỷ lệ R:R sẽ có biên dao động rất rộng so với giá trị “thực” khi áp dụng ra thị trường. Khi tăng mạnh số lượng mẫu, các ước lượng này thường hội tụ lại gần kết quả backtest ban đầu, làm cho đánh giá của bạn đáng tin hơn.

## Liên kết & Insight

Biên độ dao động ước lượng mô tả việc kết quả như [tỉ lệ thắng](../concepts/ty_le_thang) trong [backtest](../concepts/backtest) có thể “dao” rộng đến mức nào khi mẫu ít. Khi số lệnh tăng, các ước lượng thường hội tụ lại, khiến bạn bớt bị ảo giác rằng quá khứ chắc chắn lặp lại. Insight chính là: đừng chỉ nhìn điểm số backtest, hãy nhìn dải dao động—vì đó là lý do [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam) và [rủi ro thực thi](../concepts/rui_ro_thuc_thi) có thể lớn hơn bạn tưởng.

## Liên quan

* [dao\_dong\_xac\_suat](../concepts/dao_dong_xac_suat): [dao động xác suất](../concepts/dao_dong_xac_suat) quyết định độ rộng khoảng ước lượng.
* [monte\_carlo](../concepts/monte_carlo): thường dùng để ước lượng dải khả năng.
* [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam): dải dao động là lý do backtest không đảm bảo.
* [Sụp đổ xác suất](../concepts/sup_do_xac_suat): khi ước lượng sai lệch, rủi ro có thể “bùng” ở vùng xác suất thấp.