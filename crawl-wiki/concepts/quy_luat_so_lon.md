---
title: Quy luật số lớn
source_url: https://wiki.turtletrading.vn/concepts/quy_luat_so_lon
tags: []
backlinks: []
related_count: 7
crawled_at: '2026-04-21T05:01:04Z'
---

# Quy luật số lớn

Quy [luật số lớn](../concepts/luat_so_lon) mô tả rằng khi tăng số lượng quan sát (số lệnh [backtest](../concepts/backtest)), kết quả ước lượng có xu hướng ổn định hơn và ít dao động hơn so với khi mẫu nhỏ. Trong ngữ cảnh [backtest](../concepts/backtest), điều này thể hiện qua việc biên độ dao động của [tỉ lệ thắng](../concepts/ty_le_thang) thực tế thu hẹp dần khi tăng số lệnh. [📄 Nguồn](https://www.turtletrading.vn/2025/11/giai-quyet-nan-e-quy-nap-o-chac-chan.html)

## Liên kết & Insight

giải thích vì sao khi tăng số quan sát trong [backtest](../concepts/backtest), các ước lượng như [tỉ lệ thắng](../concepts/ty_le_thang) và kỳ vọng lợi nhuận thường ổn định hơn, dao động giảm dần. Nó liên hệ chặt với [dao\_dong\_xac\_suat](../concepts/dao_dong_xac_suat): mẫu lớn làm nhiễu thống kê giảm, nhưng không biến tương lai thành chắc chắn. Insight cốt lõi là: mẫu càng lớn thì bạn càng “đỡ bị lừa bởi ngẫu nhiên”, nhưng bạn vẫn phải chấp nhận bất định và kiểm tra rủi ro theo kịch bản.

## Liên quan

* [so\_mau\_du\_lon](../concepts/so_mau_du_lon): quy luật số lớn cần mẫu đủ lớn.
* [Kỳ vọng hội tụ về trung bình](../concepts/ky_vong_hoi_tu_trung_binh): kết quả hội tụ theo thời gian/mẫu.
* [dao\_dong\_xac\_suat](../concepts/dao_dong_xac_suat): dao động giảm khi tăng mẫu.
* [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam): dù quy luật số lớn giúp ổn định ước lượng, vẫn không loại bỏ bất định tương lai.