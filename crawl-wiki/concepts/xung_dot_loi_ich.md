---
title: Xung đột lợi ích
source_url: https://wiki.turtletrading.vn/concepts/xung_dot_loi_ich
tags: []
backlinks: []
related_count: 7
crawled_at: '2026-04-21T05:01:36Z'
---

# Xung đột lợi ích

Xung đột lợi ích là tình huống khi lợi ích của quỹ và trader không cùng hướng: ví dụ trader thắng thì quỹ lỗ, còn trader thua thì quỹ lãi. [📄 Nguồn](https://www.turtletrading.vn/2024/10/anh-gia-cac-mo-hinh-quy-cap-von-hien-tai_31.html)

Bài mô tả rằng trong các quỹ thử thách, quỹ có thể tìm cách khiến trader khó có lãi (tăng chi phí, dãn [spread](../concepts/spread), đẩy [trượt giá](../concepts/truot_gia), hạn chế phong cách giao dịch, kèm các quy tắc ngầm). [📄 Nguồn](https://www.turtletrading.vn/2024/10/anh-gia-cac-mo-hinh-quy-cap-von-hien-tai_31.html)

## Liên kết & Insight

Xung đột lợi ích xảy ra khi lợi ích của quỹ và trader không cùng hướng, khiến điều kiện giao dịch bị “lái” theo hướng lấy phí hoặc hạn chế lợi nhuận của trader. Trong các mô hình thử thách như [quy\_thu\_thach\_ftmo](../concepts/quy_thu_thach_ftmo), nếu cơ chế không sàng lọc tốt thì quỹ có thể tăng chi phí, dãn [spread](../concepts/spread) hay đẩy [truot\_gia](../concepts/truot_gia) để làm trader khó đạt kết quả. Ngược lại, các thiết kế như [quy\_scale\_vong\_the5ers](../concepts/quy_scale_vong_the5ers) hoặc mô hình vận hành khác có thể giảm xung đột nhờ sàng lọc dài hạn và cách chia kết quả. Insight cốt lõi là: trước khi tối ưu chiến lược, hãy tối ưu “môi trường” — vì xung đột lợi ích có thể làm mọi edge trên giấy biến mất khi vào thực chiến.

## Liên quan

* [quy\_thu\_thach\_ftmo](../concepts/quy_thu_thach_ftmo): mô hình thử thách ngắn hạn dễ phát sinh xung đột lợi ích nếu không sàng lọc được trader pro.
* [quy\_scale\_vong\_the5ers](../concepts/quy_scale_vong_the5ers): mô hình scale theo nhiều vòng có thể giảm xung đột nhờ sàng lọc dài hạn.
* [quy\_darwinex\_phat\_hanh\_von](../concepts/quy_darwinex_phat_hanh_von): bài cho rằng mô hình này ít xung đột lợi ích hơn.
* [quan\_ly\_von](../concepts/quan_ly_von): xung đột lợi ích có thể làm thay đổi điều kiện rủi ro mà trader phải quản lý.

## Ghi chú

> Contradiction
>
> Bài này cho rằng một số mô hình (ví dụ FTMO) có thể giảm xung đột lợi ích nhờ [quản lý rủi ro](../concepts/quan_ly_rui_ro) chặt và cơ chế vận hành khác; tuy nhiên các quỹ khác trong cùng nhóm có thể vẫn tạo xung đột theo hướng “lấy phí người thua”. [📄 Nguồn](https://www.turtletrading.vn/2024/10/anh-gia-cac-mo-hinh-quy-cap-von-hien-tai_31.html)