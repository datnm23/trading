---
title: Tối ưu hóa ảo giác
source_url: https://wiki.turtletrading.vn/concepts/toi_uu_ao_giac
tags: []
backlinks: []
related_count: 2
crawled_at: '2026-04-21T05:01:22Z'
---

# Tối ưu hóa ảo giác

Tối ưu hóa ảo giác là hiện tượng mô hình/chiến lược trông “tối ưu” vì dựa trên các ước lượng thống kê không phản ánh đúng rủi ro thực. Khi thị trường thuộc [extremistan](../concepts/extremistan), vài sự kiện hiếm có thể làm mean/variance/covariance ước lượng sai lệch nghiêm trọng. Kết quả là chiến lược có thể hoạt động tốt trên [backtest](../concepts/backtest) nhưng thất bại khi gặp cú sốc.

## Liên kết & Insight

Tối ưu hóa ảo giác xảy ra khi một mô hình/chiến lược “trông có vẻ tối ưu” nhờ các ước lượng thống kê đẹp, nhưng lại không phản ánh đúng rủi ro khi thị trường chuyển sang [extremistan](../concepts/extremistan). Khi đó, các tham số như trung bình và phương sai bị lệch bởi sự kiện hiếm, khiến kết quả trên [backtest](../concepts/backtest) trở nên đánh lừa. Insight cốt lõi là: đừng tin vào tối ưu hóa chỉ vì nó hợp với dữ liệu quá khứ—hãy kiểm tra độ chịu đựng trước cú sốc và giả định sai.