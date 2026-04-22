---
title: Bộ lọc trạng thái thị trường
source_url: https://wiki.turtletrading.vn/concepts/bo_loc_trang_thai
tags: []
backlinks: []
related_count: 3
crawled_at: '2026-04-21T04:59:55Z'
---

# Bộ lọc trạng thái thị trường

Bộ lọc trạng thái thị trường là phần điều kiện giúp hệ thống chỉ giao dịch khi thị trường ở “chế độ” phù hợp, ví dụ chỉ cho phép theo xu hướng khi giá nằm trong vùng xác định. Trong ví dụ Con Rùa được mô tả, trạng thái tăng/giảm/đi ngang được phân loại dựa trên vị trí giá so với các mức kháng cự-hỗ trợ và EMA. Khi [thị trường đi ngang](../concepts/thi_truong_di_ngang), hệ thống có thể đứng ngoài để giảm số lần phá vỡ thất bại. [chien\_luoc\_theo\_xu\_huong](../concepts/chien_luoc_theo_xu_huong) và [breakout](../breakout) thường cần bộ lọc để tránh nhiễu.

## Liên kết & Insight

Bộ lọc trạng thái thị trường kết nối trực tiếp với việc chọn thời điểm vào lệnh trong [chien\_luoc\_theo\_xu\_huong](../concepts/chien_luoc_theo_xu_huong) và các kịch bản [breakout](../breakout), vì nó chỉ cho hệ thống hoạt động khi thị trường đang ở “chế độ” phù hợp. Khi [thị trường đi ngang](../concepts/thi_truong_di_ngang), bộ lọc giúp giảm số lần bị nhiễu và hạn chế phá vỡ thất bại do giá liên tục quét qua các mức. Insight cốt lõi là: tín hiệu tốt nhưng vào sai “chế độ” thì vẫn thua, nên điều kiện trạng thái thường quan trọng không kém bản thân công thức vào lệnh.