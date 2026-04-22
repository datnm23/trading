---
title: Danh mục 1/N
source_url: https://wiki.turtletrading.vn/concepts/one_over_n_portfolio
tags: []
backlinks: []
related_count: 3
crawled_at: '2026-04-21T05:00:54Z'
---

# Danh mục 1/N

Danh mục 1/N là cách chia đều vốn cho N tài sản (ví dụ mỗi tài sản 1/N), không cần ước lượng mean/variance/covariance để tối ưu. [📄 Nguồn](https://www.turtletrading.vn/2026/01/ao-giac-toi-uu.html)

Bài viết nêu rằng trong dài hạn, mô hình 1/N thường xuyên đánh bại mô hình [tối ưu Markowitz](../concepts/markowitz_optimization) vì nó **không có [sai số ước lượng](../concepts/estimation_error)** bị khuếch đại bởi tối ưu hóa. [📄 Nguồn](https://www.turtletrading.vn/2026/01/ao-giac-toi-uu.html)

## Liên kết & Insight

là một lựa chọn đối lập với [markowitz\_optimization](../concepts/markowitz_optimization): thay vì tối ưu theo mean/variance/covariance, nó chia đều để tránh phải ước lượng các tham số dễ sai. Nhờ vậy nó giảm tác hại của [estimation\_error](../concepts/estimation_error) vì không có bước tối ưu nào khuếch đại sai số ước lượng. Insight cốt lõi là: trong thế giới dữ liệu không hoàn hảo, “đơn giản” đôi khi thắng “tối ưu” vì bạn không tự tạo thêm rủi ro do mô hình hóa.

## Liên quan

* [markowitz\_optimization](../concepts/markowitz_optimization): đối chiếu trực tiếp với tối ưu Markowitz.
* [estimation\_error](../concepts/estimation_error): 1/N tránh khuếch đại sai số ước lượng.
* [overfit\_vao\_qua\_khu](../concepts/overfit_vao_qua_khu): đơn giản giúp giảm overfit.
* robustness: (khái niệm liên quan) sự bền vững nhờ đơn giản.