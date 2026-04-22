---
title: Số mẫu đủ lớn tỉ lệ thắng
source_url: https://wiki.turtletrading.vn/concepts/so_mau_du_lon_ti_le_thang
tags: []
backlinks: []
related_count: 6
crawled_at: '2026-04-21T05:01:11Z'
---

# Số mẫu đủ lớn tỉ lệ thắng

> Thuộc về
>
> * [Số mẫu đủ lớn](../concepts/so_mau_du_lon)

Khi tăng số lượng lệnh [backtest](../concepts/backtest) (ví dụ từ 10 lên 100, 1.000, 10.000, 100.000), biên độ dao động của [tỉ lệ thắng](../concepts/ty_le_thang) thực tế có xu hướng thu hẹp lại và tiến gần hơn với tỉ lệ thắng quan sát trong [backtest](../concepts/backtest). Điều này cho thấy ước lượng thống kê ổn định hơn khi số mẫu lớn. [📄 Nguồn](https://www.turtletrading.vn/2025/11/giai-quyet-nan-e-quy-nap-o-chac-chan.html)

## Liên kết & Insight

Số mẫu đủ lớn tỉ lệ thắng mô tả hiệu ứng khi bạn phóng đại quy mô backtest: [ty\_le\_thang](../concepts/ty_le_thang) quan sát được sẽ dao động ít hơn và tiến gần hơn với tỉ lệ thắng thực tế. Điều này liên kết trực tiếp với ý tưởng rằng khi tăng cỡ mẫu thì [dao\_dong\_xac\_suat](../concepts/dao_dong_xac_suat) giảm, khiến ước lượng thống kê ổn định hơn. Insight quan trọng là: dù mẫu lớn giúp kết quả “đỡ nhiễu”, nó vẫn không biến backtest thành chắc chắn, nên bạn vẫn phải cảnh giác với [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam).

## Liên quan

* [so\_mau\_du\_lon](../concepts/so_mau_du_lon): nguyên lý chung về cần mẫu đủ lớn.
* [dao\_dong\_xac\_suat](../concepts/dao_dong_xac_suat): [dao động xác suất](../concepts/dao_dong_xac_suat) giảm khi tăng cỡ mẫu.
* [Kỳ vọng hội tụ về trung bình](../concepts/ky_vong_hoi_tu_trung_binh): xu hướng hội tụ khi tăng quan sát.
* [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam): dù mẫu lớn hơn vẫn không biến backtest thành “chắc chắn”.