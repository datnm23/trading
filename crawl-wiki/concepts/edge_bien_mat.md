---
title: Edge biến mất
source_url: https://wiki.turtletrading.vn/concepts/edge_bien_mat
tags: []
backlinks: []
related_count: 3
crawled_at: '2026-04-21T05:00:18Z'
---

# Edge biến mất

Edge biến mất xảy ra khi [cấu trúc thị trường](../concepts/cau_truc_thi_truong) thay đổi khiến chiến lược trước đó không còn khai thác được sai lệch. Các yếu tố như thanh khoản giảm, bot/định giá nhanh hơn, hoặc hành vi đám đông chuyển sang trạng thái khác có thể làm lợi thế suy yếu. Khi đó, [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam) trở nên đặc biệt rõ ràng vì quá khứ không còn đại diện cho hiện tại.

## Liên kết & Insight

Edge biến mất kết nối với [backtest\_khong\_bao\_dam](../concepts/backtest_khong_bao_dam) vì khi cấu trúc thị trường đổi, dữ liệu quá khứ có thể không còn đại diện cho hiện tại, khiến chiến lược từng hiệu quả suy yếu. Nó cũng thường đi kèm thay đổi trong cách thị trường vận hành như thanh khoản và hành vi đám đông, làm các sai lệch mà bạn khai thác bị thu hẹp. Insight cốt lõi là: edge không phải tài sản vĩnh viễn; nó là “điều kiện”, và khi điều kiện hết, bạn phải coi [backtest](../concepts/backtest) như tham khảo chứ không phải giấy bảo hành.