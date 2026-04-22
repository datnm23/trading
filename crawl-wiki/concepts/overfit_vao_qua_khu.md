---
title: Overfit vào quá khứ
source_url: https://wiki.turtletrading.vn/concepts/overfit_vao_qua_khu
tags: []
backlinks: []
related_count: 9
crawled_at: '2026-04-21T05:00:56Z'
---

# Overfit vào quá khứ

Overfit vào quá khứ là hiện tượng khi mô hình/chiến lược bám quá sát dữ liệu lịch sử, khiến hiệu quả ngoài mẫu giảm mạnh. Bài viết cho rằng càng cố chia/lọc state bằng [hidden\_markov\_state](../concepts/hidden_markov_state) và ML, càng dễ overfit vào quá khứ do [non\_stationarity](../concepts/non_stationarity). [📄 Nguồn](https://www.turtletrading.vn/2025/12/phan-phoi-xac-suat-extremistan-va-trend.html)

Hệ quả thường thấy là “[backtest](../concepts/backtest) ngon nhưng live toang”, vì [backtest](../concepts/backtest) thường phản ánh [phan\_phoi\_khong\_dieu\_kien](../concepts/phan_phoi_khong_dieu_kien) trong khi live phải đối mặt [phan\_phoi\_co\_dieu\_kien](../concepts/phan_phoi_co_dieu_kien). [📄 Nguồn](https://www.turtletrading.vn/2025/12/phan-phoi-xac-suat-extremistan-va-trend.html)

## Liên kết & Insight

Overfit vào quá khứ xảy ra khi chiến lược bám quá sát dữ liệu lịch sử, khiến hiệu quả ngoài mẫu suy giảm mạnh. Nó thường bị kích hoạt khi bạn cố “chia state” hoặc tinh chỉnh bằng các mô hình như [hidden\_markov\_state](../concepts/hidden_markov_state) trong bối cảnh dữ liệu vốn không ổn định, tức [non\_stationarity](../concepts/non_stationarity). Khi đó bạn dễ rơi vào cảnh “[backtest](../concepts/backtest) ngon nhưng live toang”, vì backtest phản ánh phân phối trong quá khứ còn live lại phụ thuộc bối cảnh khác đi. Insight cốt lõi là: càng tối ưu để khớp quá khứ, bạn càng phải trả giá bằng độ bền khi thị trường đổi [luật chơi](../concepts/luat_choi).

## Liên quan

* [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam): backtest không đảm bảo khi phân phối/quan hệ đổi
* [phan\_phoi\_co\_dieu\_kien](../concepts/phan_phoi_co_dieu_kien): live phụ thuộc bối cảnh
* [non\_stationarity](../concepts/non_stationarity): nguyên nhân khiến dữ liệu cũ không còn đúng
* [vong\_lap\_thay\_doi\_chien\_luoc](../concepts/vong_lap_thay_doi_chien_luoc): overfit thường kéo theo đổi chiến lược liên tục khi [drawdown](../concepts/drawdown)