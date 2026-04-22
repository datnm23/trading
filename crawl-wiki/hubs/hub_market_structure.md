---
title: Cấu trúc Thị trường
source_url: https://wiki.turtletrading.vn/hubs/hub_market_structure
tags: []
backlinks: []
related_count: 46
crawled_at: '2026-04-21T05:01:38Z'
---

# Cấu trúc Thị trường

Market structure là cách đọc “thị trường đang di chuyển như thế nào” thông qua các cấu trúc giá, trạng thái (đi ngang/xu hướng), và quan trọng hơn: ai đang cung cấp/tiêu thụ thanh khoản. Hiểu đúng cấu trúc giúp bạn bớt đoán mò và bám vào cơ chế tạo ra chuyển động giá.

## 📐 Khái niệm nền tảng

* [cau\_truc\_thi\_truong](../concepts/cau_truc_thi_truong) — Cấu trúc thị trường mô tả thị trường “di chuyển” và tạo các cấu trúc theo thời gian
* [order\_flow](../concepts/order_flow) — Order flow là dòng lệnh/nhịp tim hành vi giao dịch tác động ngược lên giá
* [so\_lenh](../concepts/so_lenh) — Sổ lệnh hiển thị lệnh chờ theo từng mức giá (BID/ASK) quyết định giá khớp
* [maker](../concepts/maker) — Maker cung cấp thanh khoản bằng lệnh chờ; giá dịch khi lệnh chờ bị “ăn” hết
* [taker](../concepts/taker) — Taker lấy đi thanh khoản bằng lệnh thị trường và nhận giá theo bid/ask tốt nhất
* [gia\_bid\_ask](../concepts/gia_bid_ask) — Bid/ask tốt nhất là hai “cửa” giá để lệnh thị trường khớp ngay
* [spread](../concepts/spread) — Spread phản ánh chi phí/độ rộng “khoảng giá” cần vượt để chuyển trạng thái
* [tinh\_thanh\_khoan](../concepts/tinh_thanh_khoan) — Tính thanh khoản quyết định giao dịch dễ/nhanh/ít tốn kém đến mức nào

## 🧱 Trạng thái & cấu trúc giá

Những gì bạn thấy trên chart thường là kết quả của việc thị trường đang ở trạng thái nào và cấu trúc nào đang được “giữ” hay “phá”.

* [thi\_truong\_di\_ngang](../concepts/thi_truong_di_ngang) — Đi ngang là cân bằng nơi lực mua/bán chưa đủ lệch để tạo chuyển động lớn
* [xu\_huong\_gia](../concepts/xu_huong_gia) — Xu hướng giá là giai đoạn thoát đi ngang khi một bên chiếm ưu thế
* [pha\_vo\_cau\_truc\_xu\_huong](../concepts/pha_vo_cau_truc_xu_huong) — Phá vỡ cấu trúc xu hướng là dấu hiệu sớm áp lực mua/bán đổi chiều
* [pha\_vo\_trang\_thai\_di\_ngang](../concepts/pha_vo_trang_thai_di_ngang) — Phá vỡ đi ngang là vượt biên nhiều lần trước khi chuyển sang trạng thái mới
* [tich\_luy\_va\_bung\_no](../concepts/tich_luy_va_bung_no) — Tích lũy và bùng nổ là nén năng lượng rồi giải phóng thành chuyển động mạnh
* [path\_dependence](../concepts/path_dependence) — Path dependence nhấn mạnh “thị trường có trí nhớ”: tương lai phụ thuộc đường giá đã đi
* [phan\_dang\_fractal\_thi\_truong](../concepts/phan_dang_fractal_thi_truong) — Thị trường phân dạng: cấu trúc lặp lại ở nhiều khung thời gian
* [history\_price](../concepts/history_price) — Giá lịch sử là “dấu vết” ảnh hưởng đến cách thị trường phản ứng về sau

## 🔥 Dòng tiền & động lực khớp lệnh

Đây là phần “vì sao giá chạy”: ai đang đẩy, ai đang rút, và thanh khoản bị tiêu thụ theo cách nào.

* [luc\_mua\_luc\_ban](../concepts/luc_mua_luc_ban) — Lực mua/lực bán là nền tảng mô tả cung cầu và xung lực giao dịch
* [luc\_mua\_ban\_chu\_dong](../concepts/luc_mua_ban_chu_dong) — Lực mua/bán chủ động là lệnh tác động trực tiếp bằng cách lấy thanh khoản
* [lenh\_chu\_dong](../concepts/lenh_chu_dong) — Lệnh chủ động (taker) làm giá dịch vì tạo mất cân bằng với lệnh chờ
* [thanh\_khoan\_bi\_dong](../concepts/thanh_khoan_bi_dong) — Thanh khoản bị động là “tường lệnh chờ” có thể bị khớp và kéo giá dịch
* [thanh\_khoan\_thap](../concepts/thanh_khoan_thap) — Thanh khoản thấp khiến giá dễ dịch hơn khi lệnh chờ mỏng
* [net\_liquidity](../concepts/net_liquidity) — Net liquidity cho biết “tiền thật” còn lại trong hệ thống có đang tăng để đổ vào tài sản không
* [dong\_tien\_lon](../concepts/dong_tien_lon) — Dòng tiền lớn ít bám chart ngắn hạn; thường tác động khi thị trường chuyển trạng thái
* [dong\_tien\_thong\_minh](../concepts/dong_tien_thong_minh) — Dòng tiền thông minh là hành vi của tổ chức/quỹ chuyên nghiệp được cho là nhạy thông tin hơn

## 🕵️ Thông tin, insider & “độ nhiễu” quan sát

Không phải mọi chuyển động đều là “dòng tiền thật”; đôi khi là độ trễ, nhiễu, hoặc cấu trúc khiến bạn nhìn sai.

* [do\_truoc\_thong\_tin](../concepts/do_truoc_thong_tin) — Độ trễ thông tin: retail phản ứng muộn nên cơ hội thường đã đi qua
* [insider\_thong\_tin\_nhay\_cam](../concepts/insider_thong_tin_nhay_cam) — Insider thông tin nhạy cảm là nhóm có quyền truy cập trước công chúng
* [giao\_dich\_noi\_gian](../concepts/giao_dich_noi_gian) — Giao dịch nội gián là hành vi insider đặt lệnh sớm để kiếm lời
* [thi\_truong\_phan\_dang](../concepts/thi_truong_phan_dang) — Thị trường phân dạng khiến bạn dễ “nhầm khung” và đọc sai ý nghĩa cấu trúc
* [nhieu\_thi\_truong](../concepts/nhieu_thi_truong) — Nhiễu thị trường là biến động ngẫu nhiên trên khung nhỏ dễ đánh lừa quyết định
* [thi\_truong\_phan\_ung\_cuc\_nhanh](../concepts/thi_truong_phan_ung_cuc_nhanh) — Thị trường phản ứng cực nhanh làm thời gian cho retail gần như không còn
* [thi\_truong\_hieu\_qua\_khong\_tuyet\_doi](../concepts/thi_truong_hieu_qua_khong_tuyet_doi) — [Thị trường hiệu quả](../concepts/thi_truong_hieu_qua) không tuyệt đối: vẫn có giai đoạn/biến cố cực đoan
* [thi\_truong\_random\_walk](../concepts/thi_truong_random_walk) — [Random walk](../concepts/random_walk) nhắc rằng nhiều biến động khó dự đoán từ quá khứ

## 🧩 Ứng dụng đọc cấu trúc theo cơ chế

Phần này giúp bạn biến “khái niệm” thành “quy trình đọc”: từ sổ lệnh/order flow đến kết luận về trạng thái.

* [order\_flow\_de\_doc](../concepts/order_flow_de_doc) — Order flow dễ đọc khi thị trường cho phép bạn diễn giải tín hiệu rõ hơn
* [khang\_cu\_ho\_tro](../concepts/khang_cu_ho_tro) — Hỗ trợ/kháng cự là cách phân loại trạng thái để hệ thống tự động ra quyết định
* [ao\_ve\_gia\_ca](../concepts/ao_ve_gia_ca) — Ảo ảnh giá cả: giá trên chart không nhất thiết phản ánh trực tiếp bản chất dòng tiền
* [ky\_vong\_gia\_ca](../concepts/ky_vong_gia_ca) — Kỳ vọng giá cả: “giá” phản ánh kỳ vọng về dòng tiền tương lai
* [ky\_vong\_tao\_gia\_tri](../concepts/ky_vong_tao_gia_tri) — Tạo giá trị trong hệ thống: giao dịch có thể đóng góp hiệu quả/phân bổ vốn, không chỉ chuyển lợi nhuận
* [fee\_capture](../concepts/fee_capture) — Fee capture: phí có thể chảy về holder/token, tạo “dòng tiền thật” thay vì chỉ doanh thu hệ thống
* [nguoi\_dung\_tra\_phi\_thuc](../concepts/nguoi_dung_tra_phi_thuc) — Người dùng trả phí thực giúp phân biệt giá trị với kỳ vọng
* [otc\_giao\_dich](../concepts/otc_giao_dich) — OTC giúp đẩy nhu cầu giao/đáp ứng ra khỏi “kho công khai”, làm thay đổi cách bạn quan sát cấu trúc

## 🎯 Bắt đầu từ đâu

Nếu mới tiếp cận domain này, đọc theo thứ tự: [cau\_truc\_thi\_truong](../concepts/cau_truc_thi_truong) → [order\_flow](../concepts/order_flow) → [so\_lenh](../concepts/so_lenh) → [maker](../concepts/maker) → [taker](../concepts/taker).

## 🔗 Hub liên quan

* [hub\_risk\_management](../hubs/hub_risk_management) — Cấu trúc thị trường và thanh khoản liên quan trực tiếp đến cách bạn đặt SL/đánh giá rủi ro khi trạng thái đổi
* [hub\_backtest\_validation](../hubs/hub_backtest_validation) — Khi bạn đọc cấu trúc/order flow, cần kiểm định xem edge có bền vững qua [regime shift](../concepts/regime_shift) không
* [hub\_trading\_systems](../hubs/hub_trading_systems) — Biến “đọc cấu trúc” thành quy tắc vào/ra lệnh và quản trị trạng thái thị trường
* [hub\_market\_structure](../hubs/hub_market_structure) — (Nếu bạn đang mở rộng) quay lại để nối các khái niệm thành bản đồ đọc thị trường thống nhất