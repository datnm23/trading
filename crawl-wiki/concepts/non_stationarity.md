---
title: Non-stationarity
source_url: https://wiki.turtletrading.vn/concepts/non_stationarity
tags: []
backlinks: []
related_count: 9
crawled_at: '2026-04-21T05:00:55Z'
---

# Non-stationarity

Non-stationarity (phi dừng) là việc bản thân định nghĩa “trạng thái” và quan hệ trong thị trường thay đổi theo thời gian. Ví dụ: trạng thái [sideway](../concepts/mediocristan) năm 2017 khác sideway năm 2024 vì thanh khoản, bot, và “player” khác nhau. [📄 Nguồn](https://www.turtletrading.vn/2025/12/phan-phoi-xac-suat-extremistan-va-trend.html)

Khi có non-stationarity, việc cố chia/lọc state bằng [hidden\_markov\_state](../concepts/hidden_markov_state) và ML có thể dẫn tới [overfit vào quá khứ](../concepts/overfit_vao_qua_khu). [📄 Nguồn](https://www.turtletrading.vn/2025/12/phan-phoi-xac-suat-extremistan-va-trend.html)

## Liên kết & Insight

Non-stationarity kết nối trực tiếp với ý tưởng rằng “trạng thái” thị trường không đứng yên, nên mọi mô hình phải chịu ảnh hưởng của [tai\_bien\_doi\_theo\_thoi\_gian](../concepts/tai_bien_doi_theo_thoi_gian) và [path\_dependence](../concepts/path_dependence): quá khứ có thể chỉ là một chương, không phải bản đồ vĩnh cửu. Khi mối quan hệ thay đổi, việc cố bắt “state” bằng các công cụ như hidden Markov hay ML dễ biến thành tối ưu cho dữ liệu cũ, dẫn tới [overfit\_vao\_qua\_khu](../concepts/overfit_vao_qua_khu). Insight cốt lõi là: nếu thị trường tự cập nhật [luật chơi](../concepts/luat_choi), thì [backtest](../concepts/backtest) hay suy luận từ quá khứ chỉ có giá trị trong một “khoảng thời gian sống” nhất định.

## Liên quan

* [tai\_bien\_doi\_theo\_thoi\_gian](../concepts/tai_bien_doi_theo_thoi_gian): [biến đổi theo thời gian](../concepts/tai_bien_doi_theo_thoi_gian) của quan hệ trong mô hình
* [path\_dependence](../concepts/path_dependence): trí nhớ làm phân phối tương lai đổi liên tục
* [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam): quá khứ không đảm bảo do quan hệ biến đổi
* [overtrading](../concepts/overtrading): tối ưu/điều chỉnh quá mức khi dữ liệu cũ không còn đúng