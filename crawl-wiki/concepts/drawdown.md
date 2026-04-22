---
title: Drawdown
source_url: https://wiki.turtletrading.vn/concepts/drawdown
tags: []
backlinks: []
related_count: 12
crawled_at: '2026-04-21T05:00:15Z'
---

# Drawdown

Drawdown là khoản chênh lệch giữa giá trị cao nhất và giá trị thấp nhất của vốn trong một khoảng thời gian. Trong giao dịch, drawdown là hệ quả tất yếu do tính bất định của thị trường và chiến lược có lợi thế vẫn có thể trải qua các [chuỗi thua lỗ](../concepts/chuoi_thua_lo) kéo dài trước khi lợi thế “phát huy”. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)

## Ý nghĩa thực hành

* Drawdown ảnh hưởng trực tiếp đến tâm lý: drawdown càng lớn càng dễ khiến người giao dịch sợ hãi và từ bỏ chiến lược. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)
* Drawdown có thể kéo dài (thậm chí 2–3 năm) nên việc “nhìn thấy [chuỗi thua lỗ](../concepts/chuoi_thua_lo)” không đồng nghĩa chiến lược đã hết lợi thế. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)

Drawdown không chỉ là “lỗ tạm thời”, mà còn là giai đoạn mà [phân phối ngẫu nhiên](../concepts/phan_phoi_ngau_nhien) của kết quả bắt đầu bộc lộ theo chuỗi (tốt xen xấu). Khi [drawdown kéo dài](../concepts/drawdown_keo_dai), niềm tin và kỷ luật thường suy giảm, khiến nhà giao dịch dễ mắc sai lầm như rời bỏ hệ thống đúng lúc lợi thế đang cần thêm mẫu. Vì vậy, [quản trị drawdown](../concepts/quan_tri_drawdown) thực chất là quản trị khả năng tiếp tục giao dịch đủ lâu để lợi thế phát huy.

Trong các chương trình cấp vốn, [max drawdown](../concepts/max_drawdown) thường được dùng như “giới hạn sống còn” để quyết định có được rút lợi nhuận hay không. Vì vậy, trader cần hiểu drawdown không chỉ là con số trên báo cáo mà còn là ràng buộc vận hành: chỉ cần vượt ngưỡng do lệch hệ thống hoặc biến động bất lợi là có thể bị dừng tài khoản.

Drawdown không chỉ là “thua lỗ tạm thời”, mà còn là thước đo sức chịu đựng của hệ thống trước chuỗi kết quả ngẫu nhiên. Khi [drawdown kéo dài](../concepts/drawdown_keo_dai), nhà giao dịch dễ nhầm rằng lợi thế đã biến mất, dù thực tế chỉ là phân phối xác suất đang đi qua giai đoạn bất lợi. Vì vậy, [quản trị drawdown](../concepts/quan_tri_drawdown) thường quan trọng không kém việc tối ưu lợi nhuận kỳ vọng.

Trong thực tế, thua lỗ thường leo thang không chỉ do biến động giá mà còn do hành vi bám víu vào hy vọng (không cắt lỗ đúng kế hoạch). Khi chuỗi thua lỗ ngắn hạn xảy ra, tâm lý dễ làm bạn đổi chiến lược giữa chừng, khiến drawdown kéo dài hơn dự tính.

Trong các chiến lược dựa trên kỳ vọng, drawdown thường là “giá phải trả” để đi qua chuỗi [phân phối ngẫu nhiên](../concepts/phan_phoi_ngau_nhien). Việc đo drawdown theo thời gian (không chỉ theo mức) giúp bạn đánh giá khả năng sống sót của hệ thống khi gặp kịch bản xấu.

Trong các chiến lược có [đòn bẩy](../concepts/don_bay) và phụ thuộc tỷ giá, drawdown có thể đến theo “hai tầng”: một tầng từ biến động giá tài sản và một tầng từ biến động tỷ giá làm tăng giá trị khoản nợ. Vì vậy, mức giảm có thể vượt xa kỳ vọng nếu [backtest](../concepts/backtest) không mô phỏng đồng thời cả hai nguồn rủi ro.

Trong thế giới phi tuyến, drawdown không chỉ là mức lỗ tối đa mà còn là “thời gian bị kẹt” trước khi hồi phục. Một hệ thống có drawdown ngắn nhưng hồi phục chậm vẫn có thể khiến bạn mất khả năng tái nạp vốn hoặc buộc phải cắt lỗ sai thời điểm. Do đó, đánh giá drawdown nên đi kèm tốc độ phục hồi và khả năng chịu đựng theo chuỗi.

Drawdown không chỉ là “thua lỗ” mà còn là phép thử khả năng chịu đựng của hệ thống và kỷ luật của người dùng. Nếu bạn không thể đứng dậy sau một chu kỳ thua, thì mọi kỳ vọng lợi nhuận dài hạn gần như không còn ý nghĩa. Vì vậy, mục tiêu thực tế là thiết kế để drawdown trở thành chi phí vận hành có thể chịu được, thay vì biến thành thảm họa tâm lý.

Drawdown trong thị trường [đuôi béo](../concepts/duoi_beo) không chỉ là chuỗi thua lỗ dần dần, mà có thể đến từ một cú nhảy giá (gap/flash crash) làm chiến lược chịu tổn thất vượt xa kỳ vọng. Do đó, quản trị rủi ro nên ưu tiên kịch bản xấu hiếm gặp thay vì chỉ tối ưu theo mức biến động trung bình.

## Liên kết & Insight

Drawdown là khoảng lùi giữa đỉnh và đáy của vốn, nên nó thường đi kèm với cảm giác “chiến lược không còn đúng” dù kỳ vọng dài hạn vẫn có thể dương. Khi drawdown kéo dài, người ta nhìn thấy [chuoi\_thua\_lo](../concepts/chuoi_thua_lo) theo cụm và dễ nhầm rằng lợi thế đã biến mất, trong khi thực tế đó có thể chỉ là giai đoạn phân phối ngẫu nhiên đang “xấu xen tốt” và cần thêm mẫu để lợi thế phát huy. Insight cốt lõi là quản trị drawdown không chỉ để giảm lỗ, mà để đảm bảo bạn đủ kỷ luật và đủ thời gian sống sót qua chuỗi bất lợi, giống như [quan\_tri\_drawdown](../concepts/quan_tri_drawdown)—đặt giới hạn hành động để không rời bỏ hệ thống đúng lúc nó đang cần thêm dữ liệu.

## Liên quan

* [quan\_ly\_rui\_ro](../concepts/quan_ly_rui_ro): quản trị drawdown bằng dừng lỗ và điều chỉnh khối lượng. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)
* [dung\_lo](../concepts/dung_lo): công cụ để giới hạn mức drawdown có thể xảy ra. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)
* [risk\_of\_ruin](../concepts/risk_of_ruin): drawdown lớn làm tăng xác suất “phá sản” nếu không [quản lý rủi ro](../concepts/quan_ly_rui_ro). [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)
* [ao\_tuong\_kiem\_soat](../concepts/ao_tuong_kiem_soat): con người dễ ảo tưởng rằng có thể kiểm soát hoàn toàn kết quả, trong khi drawdown là không thể tránh né. [📄 Nguồn](https://www.turtletrading.vn/2025/01/vuot-qua-drawdown-rao-can-lon-nhat-ngan.html)