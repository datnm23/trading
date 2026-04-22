---
title: Quản lý Rủi ro
source_url: https://wiki.turtletrading.vn/hubs/hub_risk_management
tags: []
backlinks: []
related_count: 49
crawled_at: '2026-04-21T05:01:38Z'
---

# Quản lý Rủi ro

Risk management là “hệ thống sinh tồn” của giao dịch: bạn không chỉ cần chiến lược có kỳ vọng, mà còn phải kiểm soát cách rủi ro tích lũy theo thời gian để không bị loại khỏi cuộc chơi. Trong thực tế, phần lớn thất bại đến từ drawdown, đuôi rủi ro và sai lệch thực thi—không phải vì thiếu một vài điểm vào lệnh.

## 📐 Khái niệm nền tảng

Nắm các khái niệm cốt lõi để hiểu “rủi ro là gì” và “đo bằng gì”.

* [quan\_ly\_rui\_ro](../concepts/quan_ly_rui_ro) — Giảm thiểu tổn thất khi thị trường đi ngược dự đoán
* [drawdown](../concepts/drawdown) — Mức sụt giảm từ đỉnh vốn đến đáy vốn trong một giai đoạn
* [max\_drawdown](../concepts/max_drawdown) — Ngưỡng drawdown tối đa cần kiểm soát để tránh phá kỷ luật
* [risk\_of\_ruin](../concepts/risk_of_ruin) — Nguy cơ mất khả năng tồn tại do rủi ro tích lũy quá lớn
* [rui\_ro\_tren\_moi\_lenh](../concepts/rui_ro_tren_moi_lenh) — Rủi ro trên mỗi lệnh (để không “đốt” tài khoản chỉ vì một sai lầm)
* [dung\_lo](../concepts/dung_lo) — Mức giới hạn thua lỗ tối đa cho mỗi giao dịch/lệnh

## 🧱 Thiết kế giới hạn thua lỗ & kiểm soát drawdown

Phần này trả lời: “Nếu sai, mình sai tới đâu và sai như thế nào để vẫn sống sót?”

* [lenh\_cat\_lo](../concepts/lenh_cat_lo) — Lệnh cắt lỗ kích hoạt theo mức giá để giới hạn tổn thất
* [cat\_lo\_nghiem\_ngat](../concepts/cat_lo_nghiem_ngat) — Cắt lỗ nghiêm ngặt như cơ chế bảo hiểm cho sự kiện hiếm
* [dung\_lo\_theo\_atr](../concepts/dung_lo_theo_atr) — Đặt dừng lỗ theo ATR để chuẩn hóa khoảng cách theo biến động
* [doi\_dung\_lo\_theo\_vung\_gia\_buon](../concepts/doi_dung_lo_theo_vung_gia_buon) — Dời dừng lỗ theo vùng giá lớn để bám theo [cấu trúc thị trường](../concepts/cau_truc_thi_truong)
* [chien\_luoc\_cat\_lo\_chay\_loi](../concepts/chien_luoc_cat_lo_chay_loi) — Cắt lỗ nhanh nhưng cho phép lệnh có lợi chạy xa
* [chien\_luoc\_gong\_lo](../concepts/chien_luoc_gong_lo) — Gồng lỗ khiến [rủi ro đuôi](../concepts/tail_risk) trái phình to
* [chien\_luoc\_khong\_cat\_lo](../concepts/chien_luoc_khong_cat_lo) — Không cắt lỗ/cắt lỗ không đủ sớm làm thua lỗ “không có giới hạn”
* [quan\_ly\_drawdown](../concepts/quan_ly_drawdown) — Giữ drawdown trong “vùng cho phép” để không bị cuốn vào rút lui sớm

## 📉 Rủi ro đuôi, bất định & sai lệch mô hình

Đây là phần “đừng tin quá mức”: thị trường có thể lệch khỏi trung bình và [backtest](../concepts/backtest).

* [tail\_risk](../concepts/tail_risk) — Rủi ro đuôi: sự kiện cực đoan nằm ở phần “đuôi” của phân phối
* [rui\_ro\_duoi\_trai](../concepts/rui_ro_duoi_trai) — Đuôi trái: phần tệ nhất có thể không bị cắt bỏ hoàn toàn chỉ bằng dừng lỗ
* [duoi\_beo\_trong\_giao\_dich](../concepts/duoi_beo_trong_giao_dich) — [Đuôi béo](../concepts/duoi_beo) xảy ra thường xuyên hơn giả định chuẩn, làm thống kê bị lệch
* [phan\_phoi\_duoi\_beo\_trong\_thi\_truong](../concepts/phan_phoi_duoi_beo_trong_thi_truong) — Các “mẫu hình” có vẻ quy luật có thể chỉ là hệ quả của fat tail
* [black\_swan](../concepts/black_swan) — [Thiên nga đen](../concepts/thi_truong_thien_nga_den): sự kiện cực đoan vừa khó tiên đoán vừa [tác động hệ thống](../concepts/tac_dong_he_thong)
* [gray\_swan](../concepts/gray_swan) — Thiên nga xám: có thể đã có cảnh báo nhưng vẫn là biến động lớn
* [khong\_the\_bao\_dam\_tuong\_lai](../concepts/khong_the_bao_dam_tuong_lai) — Không thể bảo đảm tương lai: hệ thống tốt hôm nay có thể lỗi thời
* [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam) — Backtest không bảo đảm: quá khứ chỉ là ước lượng trong bất định

## 🧮 Position sizing & cấu trúc phân bổ rủi ro

Phần này trả lời: “Mình đặt bao nhiêu tiền cho mỗi kịch bản sai?”

* [quan\_ly\_von](../concepts/quan_ly_von) — Quản lý vốn và lệnh mở như một phần của hệ thống kiểm soát rủi ro
* [ky\_quy\_phan\_tram](../concepts/ky_quy_phan_tram) — Ký quỹ theo tỷ lệ phần trăm để giảm rủi ro khi biến động mạnh
* [don\_bay](../concepts/don_bay) — Đòn bẩy: công cụ khuếch đại nhưng quan trọng hơn là cơ chế bảo vệ nguồn vốn nếu dùng đúng
* [don\_bay\_khong\_phai\_cong\_cu\_ma\_thuat](../concepts/don_bay_khong_phai_cong_cu_ma_thuat) — Đòn bẩy không phải “ma thuật”: có thể xóa sạch tài khoản nhanh
* [tang\_rui\_ro\_theo\_giai\_doan](../concepts/tang_rui_ro_theo_giai_doan) — Tăng rủi ro theo giai đoạn để cân bằng tốc độ tăng trưởng và sống sót
* [tang\_truong\_nguon\_von\_nhanh](../concepts/tang_truong_nguon_von_nhanh) — Tăng trưởng nhanh thường đánh đổi bằng rủi ro cao hơn (cần kiểm soát chặt)
* [tap\_trung\_hoa](../concepts/tap_trung_hoa) — Tập trung hóa: tăng xác suất “đúng lớn”, nhưng cũng làm rủi ro tập trung hơn
* [da\_dang\_hoa\_danh\_muc](../concepts/da_dang_hoa_danh_muc) — Đa dạng hóa danh mục để tránh phụ thuộc một kịch bản [may mắn](../concepts/may_man)

## 🧪 Thực thi, chi phí & vận hành hệ thống rủi ro

Rủi ro không chỉ nằm trong lý thuyết—nó nằm ở trượt giá, phí và cách bạn vận hành.

* [truot\_gia](../concepts/truot_gia) — Trượt giá làm kết quả thực tế lệch khỏi tính toán
* [spread](../concepts/spread) — Spread là “chi phí ẩn” nằm trong giá bid/ask
* [chi\_phi\_giao\_dich](../concepts/chi_phi_giao_dich) — Chi phí giao dịch (phí, hoa hồng, hao hụt do chênh lệch)
* [chi\_phi\_thuc\_te\_backtest](../concepts/chi_phi_thuc_te_backtest) — Backtest thường lạc quan vì chi phí thực thi bị đánh giá thấp
* [giam\_giao\_dich\_qua\_muc](../concepts/giam_giao_dich_qua_muc) — [Overtrading](../concepts/overtrading) làm bạn phá kỷ luật và tăng chi phí/độ nhiễu
* [van\_hanh\_theo\_dieu\_kien](../concepts/van_hanh_theo_dieu_kien) — Vận hành theo điều kiện để tránh quyết định tùy hứng khi thị trường biến động
* [giam\_sat\_phan\_hoi](../concepts/giam_sat_phan_hoi) — Giám sát phản hồi khi chạy ngoài đời để phát hiện bất thường
* [nhat\_ky\_giao\_dich](../concepts/nhat_ky_giao_dich) — Nhật ký giao dịch để truy vết “vì sao rủi ro xảy ra” và sửa quy trình

## 🎯 Bắt đầu từ đâu

Nếu mới tiếp cận domain này, đọc theo thứ tự: [quan\_ly\_rui\_ro\_truoc](../concepts/quan_ly_rui_ro_truoc) → [drawdown](../concepts/drawdown) → [max\_drawdown](../concepts/max_drawdown) → [dung\_lo](../concepts/dung_lo) → [risk\_of\_ruin](../concepts/risk_of_ruin)

## 🔗 Hub liên quan

* [hub\_risk\_management](../hubs/hub_risk_management) — (Chính hub này) để đi sâu vào drawdown, dừng lỗ, sizing và risk of ruin
* [hub\_backtest\_validation](../hubs/hub_backtest_validation) — Vì quản lý rủi ro phụ thuộc mạnh vào việc kiểm định giả định (và hiểu backtest không bảo đảm)
* [hub\_trading\_systems](../hubs/hub_trading_systems) — Quản trị rủi ro hiệu quả thường là một tầng trong hệ thống vận hành (logic → rủi ro → tâm lý)
* [hub\_trading\_psychology](../hubs/hub_trading_psychology) — Drawdown và cắt lỗ thất bại thường là vấn đề tâm lý/kỷ luật, không chỉ là kỹ thuật