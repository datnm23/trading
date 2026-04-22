---
title: Zero-knowledge proof
source_url: https://wiki.turtletrading.vn/concepts/zero_knowledge_proof
tags: []
backlinks: []
related_count: 4
crawled_at: '2026-04-21T05:01:36Z'
---

# Zero-knowledge proof

Zero-knowledge proof (ZK proof) là cơ chế mật mã cho phép tạo ra **bằng chứng toán học** rằng một phép tính/chương trình đã chạy đúng, mà không cần tiết lộ chi tiết bên trong. Trong bài viết, ZK proof được dùng để thay thế việc để mọi node chạy lại code: chỉ cần một máy chạy và tạo bằng chứng, các node còn lại xác minh bằng chứng đó. [📄 Nguồn](https://www.turtletrading.vn/2026/03/tri-tue-nhan-tao-blockchain-va-ich-en.html)

## Liên kết & Insight

kết nối trực tiếp với ý tưởng [trustless\_computation](../concepts/trustless_computation): thay vì phải tin vào việc mọi bên chạy đúng, hệ thống chỉ cần tin vào bằng chứng toán học. Nó cũng đi cùng mô hình [off\_chain\_on\_chain](../concepts/off_chain_on_chain), nơi tính toán diễn ra ngoài chuỗi rồi dùng ZK để “đóng dấu” tính đúng trước khi xác minh trên chuỗi. Insight cốt lõi là: ZK giúp giảm nhu cầu kiểm chứng bằng cách lặp lại toàn bộ quy trình, từ đó biến sự đúng đắn thành thứ có thể kiểm tra nhanh mà không lộ chi tiết.

## Liên quan

* [trustless\_computation](../concepts/trustless_computation): ZK proof là nền tảng để hiện thực hóa kiểm chứng không cần tin hệ thống vận hành. [📄 Nguồn](https://www.turtletrading.vn/2026/03/tri-tue-nhan-tao-blockchain-va-ich-en.html)
* [off\_chain\_on\_chain](../concepts/off_chain_on_chain): tính toán có thể diễn ra off-chain, sau đó dùng ZK để xác minh on-chain. [📄 Nguồn](https://www.turtletrading.vn/2026/03/tri-tue-nhan-tao-blockchain-va-ich-en.html)
* [blockchain\_trilemma](../concepts/blockchain_trilemma): bài viết đối chiếu cách [blockchain](../concepts/blockchain) truyền thống tốn tài nguyên với hướng ZK giúp giảm chi phí xác minh. [📄 Nguồn](https://www.turtletrading.vn/2026/03/tri-tue-nhan-tao-blockchain-va-ich-en.html)