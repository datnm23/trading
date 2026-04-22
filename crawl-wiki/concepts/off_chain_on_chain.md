---
title: Off-chain on-chain
source_url: https://wiki.turtletrading.vn/concepts/off_chain_on_chain
tags: []
backlinks: []
related_count: 4
crawled_at: '2026-04-21T05:00:54Z'
---

# Off-chain on-chain

Off-chain on-chain là mô hình trong đó **tính toán** diễn ra ở ngoài chuỗi (off-chain), còn **xác minh** diễn ra trên chuỗi (on-chain). Bài viết mô tả xu hướng dịch chuyển: nhiều tác vụ không còn cần chạy on-chain real-time, mà chuyển sang “tính toán off-chain ⇒ xác minh bằng on-chain”, nhờ các cơ chế như ZK proof. [📄 Nguồn](https://www.turtletrading.vn/2026/03/tri-tue-nhan-tao-blockchain-va-ich-en.html)

## Liên kết & Insight

kết nối trực tiếp với [zero\_knowledge\_proof](../concepts/zero_knowledge_proof) ở chỗ: thay vì chạy mọi thứ on-chain, hệ thống tạo bằng chứng off-chain rồi on-chain chỉ cần xác minh nhanh và rẻ. Nó cũng liên hệ với [trustless\_computation](../concepts/trustless_computation) vì mục tiêu là giảm niềm tin vào “cách vận hành” của bên thực hiện, chuyển sang tin vào tính đúng của bằng chứng. Insight cốt lõi là: khi bạn tách “tính toán” và “xác minh”, bạn có thể vừa giảm chi phí/độ trễ vừa giữ được tính kiểm chứng, thay vì phải gánh toàn bộ lên [blockchain](../concepts/blockchain).

## Liên quan

* [zero\_knowledge\_proof](../concepts/zero_knowledge_proof): ZK proof là cách tạo bằng chứng để on-chain xác minh rẻ. [📄 Nguồn](https://www.turtletrading.vn/2026/03/tri-tue-nhan-tao-blockchain-va-ich-en.html)
* [trustless\_computation](../concepts/trustless_computation): mô hình này là cách hiện thực hóa kiểm chứng không cần tin vào hệ thống vận hành. [📄 Nguồn](https://www.turtletrading.vn/2026/03/tri-tue-nhan-tao-blockchain-va-ich-en.html)
* [blockchain\_trilemma](../concepts/blockchain_trilemma): đối chiếu với cách truyền thống phải chạy lại đồng loạt gây phí/latency cao. [📄 Nguồn](https://www.turtletrading.vn/2026/03/tri-tue-nhan-tao-blockchain-va-ich-en.html)