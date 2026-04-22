---
title: Giả định Gaussian
source_url: https://wiki.turtletrading.vn/concepts/gaussian_assumption
tags: []
backlinks: []
related_count: 5
crawled_at: '2026-04-21T05:00:20Z'
---

# Giả định Gaussian

Giả định Gaussian là kỳ vọng rằng lợi nhuận/biến động có phân phối gần chuẩn Gauss, từ đó mean/variance và các công cụ thống kê như Markowitz có ý nghĩa và hội tụ tốt. [📄 Nguồn](https://www.turtletrading.vn/2026/01/ao-giac-toi-uu.html)

Bài viết lập luận rằng trong [Extremistan](../concepts/extremistan), giả định này không thỏa: đuôi dày (fat tails) khiến variance có thể không tồn tại hoặc cực kỳ nhạy với outlier, làm tối ưu hóa dựa trên thống kê trở nên vô dụng. [📄 Nguồn](https://www.turtletrading.vn/2026/01/ao-giac-toi-uu.html)

Giả định Gaussian thường ngầm coi đuôi phân phối đủ mỏng để phương sai/độ lệch chuẩn phản ánh đúng mức rủi ro “thông thường”. Khi thị trường có fat tails, việc dùng các công thức dựa trên mean-variance có thể biến rủi ro thực tế thành một con số “đẹp nhưng sai”.

## Liên kết & Insight

Giả định Gaussian liên kết với các mô hình thống kê và tối ưu hóa dựa trên mean/variance, nên nó là nền tảng ngầm cho nhiều cách đo rủi ro “trông có vẻ hợp lý”. Nhưng khi thị trường rơi vào vùng đuôi dày, giả định này gãy vì outlier có thể làm phương sai không ổn định hoặc thậm chí không phản ánh đúng rủi ro thực. Insight cốt lõi là trong [phan\_phoi\_duoi\_beo](../concepts/phan_phoi_duoi_beo) bạn không thể dùng các công thức “đẹp” để thay cho việc hiểu xác suất cực đoan, và điều đó làm [markowitz\_optimization](../concepts/markowitz_optimization) dễ cho kết quả sai nếu dữ liệu không đủ “gần chuẩn”.

## Liên quan

* [phan\_phoi\_duoi\_beo](../concepts/phan_phoi_duoi_beo): fat tails làm giả định Gaussian gãy.
* [mediocristan](../concepts/mediocristan): nơi giả định Gaussian thường hợp lý hơn.
* [markowitz\_optimization](../concepts/markowitz_optimization): Markowitz phụ thuộc vào mean/variance/covariance ổn định.
* [optimizing\_in\_extremistan](../concepts/optimizing_in_extremistan): giải thích thất bại khi áp dụng Gaussian vào [Extremistan](../concepts/extremistan).