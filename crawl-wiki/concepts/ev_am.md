---
title: EV âm
source_url: https://wiki.turtletrading.vn/concepts/ev_am
tags: []
backlinks: []
related_count: 8
crawled_at: '2026-04-21T05:00:19Z'
---

# EV âm

EV âm là trường hợp giá trị kỳ vọng của chiến lược nhỏ hơn 0, tức về dài hạn chiến lược có xu hướng thua. [📄 Nguồn](https://www.turtletrading.vn/2026/01/giai-ma-tam-ly-giao-dich.html)

Bài viết dùng ví dụ winrate 90% nhưng RR 1/10 và risk mỗi lệnh 0.1% để minh họa EV = 0.9×1 - 0.1×10 = -0.1 (âm). [📄 Nguồn](https://www.turtletrading.vn/2026/01/giai-ma-tam-ly-giao-dich.html)

Ngay cả khi một chiến lược trông có vẻ “đúng” trong quá khứ, EV có thể vẫn âm do [chi phí giao dịch](../concepts/chi_phi_giao_dich), [trượt giá](../concepts/truot_gia), sai lệch ước lượng và các rủi ro hiếm nhưng nặng. Khi EV âm, càng giao dịch nhiều thường càng làm lộ rõ xu hướng thua lỗ dài hạn.

Bài viết nhấn mạnh rằng nhiều trò “đặt cược” trong tài chính (như roulette, lô đề, hay các sản phẩm có phí/điều khoản bất lợi) thường có EV âm cho người tham gia. Khi EV âm, càng tăng số lần tham gia thì kết quả kỳ vọng càng bất lợi, vì [luật chơi](../concepts/luat_choi) đã được thiết kế theo hướng lấy phần thắng từ phía người chơi.

## Liên kết & Insight

EV âm mô tả trường hợp kỳ vọng dài hạn của chiến lược nhỏ hơn 0, nghĩa là về lâu dài bạn có xu hướng thua dù từng lệnh có thể thắng. Nó liên kết chặt với [ky\_vong\_am](../concepts/ky_vong_am) và công thức [gia\_tri\_ky\_vong\_ev](../concepts/gia_tri_ky_vong_ev): khi EV âm, càng tăng số lần tham gia thì kết quả kỳ vọng càng bất lợi, giống như các trò chơi được thiết kế để lấy phần thắng từ phía người chơi. Insight cốt lõi là: đừng bị đánh lừa bởi winrate cao—nếu RR và chi phí/điều khoản làm EV âm, bạn đang “trả học phí” cho một xu hướng thua dài hạn.

## Liên quan

* [ky\_vong\_am](../concepts/ky_vong_am): cách gọi tương đương trong ngữ cảnh trading.
* [gia\_tri\_ky\_vong\_ev](../concepts/gia_tri_ky_vong_ev): công thức/khái niệm EV.
* [ky\_vong\_loi\_nhuan\_ev\_duong](../concepts/ky_vong_loi_nhuan_ev_duong): đối lập EV âm.
* [quan\_ly\_rui\_ro](../concepts/quan_ly_rui_ro): EV âm vẫn có thể gây “[cháy tài khoản](../concepts/chay_tai_khoan)” nếu [quản lý rủi ro](../concepts/quan_ly_rui_ro) kém.