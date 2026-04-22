---
title: Crypto & Blockchain
source_url: https://wiki.turtletrading.vn/hubs/hub_crypto_blockchain
tags: []
backlinks: []
related_count: 38
crawled_at: '2026-04-21T05:01:37Z'
---

# Crypto & Blockchain

Crypto & blockchain là lĩnh vực xây “niềm tin không cần tin người”: dữ liệu và giao dịch được ghi nhận theo chuỗi, vận hành nhờ cơ chế đồng thuận và có thể kiểm chứng bằng mật mã + dữ liệu on-chain. Nó quan trọng vì vừa là hạ tầng (blockchain, PoW, trustless) vừa là nơi phát sinh kinh tế mới (DeFi, stablecoin, token hóa).

## 📐 Khái niệm nền tảng

Nắm các khối “xương sống” để hiểu vì sao blockchain có thể vận hành trustless.

* [blockchain](../concepts/blockchain) — Nền tảng ghi nhận dữ liệu theo chuỗi khối, hướng tới “khó sửa/xóa tùy tiện”
* [trustless](../concepts/trustless) — Thiết kế hệ thống không cần tin vào một cá nhân cụ thể, dựa vào cơ chế/thuật toán
* [pow](../concepts/pow) — Proof of Work: đồng thuận bằng việc tiêu tốn năng lượng để đạt thống nhất mạng
* [tinh\_bat\_bien](../concepts/tinh_bat_bien) — Tính bất biến: dữ liệu khó bị thay đổi nhờ cơ chế bảo mật
* [phi\_thuc\_dung\_mang](../concepts/phi_thuc_dung_mang) — Phí thực dùng mạng: phí phản ánh nhu cầu sử dụng thật, liên quan khả năng nuôi miner khi block\_reward giảm

## 🧱 Hạ tầng & cơ chế vận hành

Hiểu cách mạng tạo đồng thuận, tạo tiền, và “nối” thế giới ngoài chuỗi vào trong.

* [bitcoin\_miner](../concepts/bitcoin_miner) — Miner tham gia tạo block và nhận phần thưởng, duy trì cơ chế PoW
* [block\_reward](../concepts/block_reward) — Phần thưởng block; giảm theo chu kỳ và hướng tới giới hạn cung
* [hashpower\_suy\_giam](../concepts/hashpower_suy_giam) — Hashpower suy giảm khi miner rời mạng do lợi nhuận không còn hấp dẫn
* [trust\_layer](../concepts/trust_layer) — Blockchain như “trust layer” xác minh/giám sát thay vì mọi logic ứng dụng đều tự chạy
* [oracle](../concepts/oracle) — Oracle: cầu nối on-chain ⇐> off-chain để token hóa tài sản/logic có dữ liệu ngoài chuỗi
* [off\_chain\_on\_chain](../concepts/off_chain_on_chain) — Off-chain on-chain: tính toán ngoài chuỗi, xác minh trên chuỗi để tối ưu hiệu năng
* [trustless\_computation](../concepts/trustless_computation) — Kết quả tính toán có thể được kiểm chứng mà không cần tin hệ thống tập trung

## 🪙 Stablecoin & token hóa giá trị

Tập trung vào cách giá trị được “đóng gói” thành token và trở thành nhiên liệu cho dòng tiền trên chain.

* [stablecoin](../concepts/stablecoin) — Stablecoin tạo lớp token có thể dùng như phương tiện/điểm khởi đầu cho dòng tiền trên chain
* [token\_hoa\_tai\_san](../concepts/token_hoa_tai_san) — Token hóa tài sản: đưa tài sản ngoài đời lên blockchain để mở cách huy động/vận hành vốn
* [stablecoin\_neo\_usd](../concepts/stablecoin_neo_usd) — Thiết kế stablecoin bám USD để “xuất khẩu đô la” và giữ giả định thanh khoản USD
* [crypto\_tien\_di\_chuyen\_gia\_tri](../concepts/crypto_tien_di_chuyen_gia_tri) — Vai trò cốt lõi: gửi/xác minh/thanh toán giá trị không phụ thuộc hoàn toàn trung gian
* [cash\_settlement](../concepts/cash_settlement) — Cash-settlement: thay vì giao nhận ngay, hệ thống có thể thanh toán bằng tiền mặt để xử lý yêu cầu

## 🧠 DeFi & kinh tế on-chain

Đi từ “hạ tầng” sang “hệ sinh thái”: giao dịch, tạo lợi nhuận, và cách đo xem có giá trị thật hay không.

* [giao\_dich\_phi\_tap\_trung](../concepts/giao_dich_phi_tap_trung) — Giao dịch phi tập trung: swap, [phái sinh](../concepts/phai_sinh), lending/stake, tạo stablecoin bằng tài sản thế chấp
* [defi\_analytics\_onchain](../concepts/defi_analytics_onchain) — Analytics onchain: quan sát TVL/fees/revenue/volume/yields để suy ra nhu cầu thật
* [nguoi\_dung\_tra\_phi\_thuc](../concepts/nguoi_dung_tra_phi_thuc) — Người dùng trả phí thực: phân biệt “giá trị” với “kỳ vọng” bằng dòng tiền thật
* [fee\_capture](../concepts/fee_capture) — Fee-capture: phí chảy về token/holder thay vì chỉ tạo doanh thu mơ hồ cho hệ thống
* [incentive\_dong\_tien\_ao](../concepts/incentive_dong_tien_ao) — Incentive dòng tiền ảo: lợi nhuận đến từ incentive “tự in” thay vì người dùng trả phí thật
* [token\_value\_vs\_price](../concepts/token_value_vs_price) — Token value vs price: token tăng giá không đồng nghĩa có giá trị nếu thiếu nhu cầu/fee thật
* [phan\_tich\_cau\_truc\_tao\_gia\_tri](../concepts/phan_tich_cau_truc_tao_gia_tri) — Phân tích cấu trúc tạo giá trị: bắt đầu từ “dự án tạo ra giá trị thế nào” thay vì chỉ nhìn chart

## 📊 Đo lường, định giá & chu kỳ

Dùng dữ liệu on-chain để định giá, đọc chu kỳ và tránh bị narrative lấn át.

* [mvrv](../concepts/mvrv) — MVRV (on-chain): so giá thị trường với “giá vốn thực” (giá mua trung bình)
* [dinh\_gia\_coin](../concepts/dinh_gia_coin) — Định giá coin theo on-chain: dùng MVRV để nhận diện quá cao/quá thấp
* [chu\_ky\_4\_nam\_bitcoin](../concepts/chu_ky_4_nam_bitcoin) — Chu kỳ 4 năm Bitcoin: xoay quanh bitcoin\_halving và các pha bull/bear/tích lũy/phục hồi
* [giai\_doan\_bull\_market](../concepts/giai_doan_bull_market) — Bull market: pha tăng mạnh sau bitcoin\_halving, thường đạt đỉnh trong chu kỳ
* [giai\_doan\_bear\_market](../concepts/giai_doan_bear_market) — Bear market: pha điều chỉnh sâu sau bull market
* [giam\_toc\_tang\_truong](../concepts/giam_toc_tang_truong) — Giảm tốc tăng trưởng: % tăng trưởng có xu hướng giảm khi vốn hóa lớn dần
* [bitcoin\_halving](../concepts/bitcoin_halving) — Bitcoin halving: phần thưởng miner giảm một nửa, thường được xem là mốc quan trọng

## 🎯 Bắt đầu từ đâu

Nếu mới tiếp cận domain này, đọc theo thứ tự: [trustless](../concepts/trustless) → [blockchain](../concepts/blockchain) → [pow](../concepts/pow) → [stablecoin](../concepts/stablecoin) → [defi\_analytics\_onchain](../concepts/defi_analytics_onchain)

## 🔗 Hub liên quan

* [hub\_risk\_management](../hubs/hub_risk_management) — Crypto/DeFi phụ thuộc mạnh vào dữ liệu on-chain và rủi ro cấu trúc, nên đi kèm tư duy [quản lý rủi ro](../concepts/quan_ly_rui_ro)
* [hub\_backtest\_validation](../hubs/hub_backtest_validation) — Khi dùng chỉ số/metrics on-chain để ra quyết định, cần kiểm định lại bằng [backtest](../concepts/backtest)
* [hub\_statistics](../hubs/hub_statistics) — Nhiều “đọc on-chain” thực chất là suy luận xác suất/định lượng, nên cần nền thống kê
* [hub\_trading\_systems](../hubs/hub_trading_systems) — Nếu bạn biến dữ liệu on-chain thành tín hiệu, sẽ sớm chạm tới việc thiết kế hệ thống giao dịch