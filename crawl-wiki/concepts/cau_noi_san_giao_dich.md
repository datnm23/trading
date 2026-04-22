---
title: Cầu nối sàn giao dịch
source_url: https://wiki.turtletrading.vn/concepts/cau_noi_san_giao_dich
tags: []
backlinks: []
related_count: 5
crawled_at: '2026-04-21T04:59:59Z'
---

# Cầu nối sàn giao dịch

Cầu nối sàn giao dịch là lớp trung gian giúp chuyển quyết định của hệ thống thành hành động có thể thực hiện trên từng sàn, đồng thời mang thông tin phản hồi từ sàn quay ngược về hệ thống. Vì mỗi sàn có cách giao tiếp, định dạng dữ liệu, gửi lệnh, trả trạng thái lệnh và xử lý lỗi khác nhau, cầu nối giúp chuẩn hóa liên lạc để hệ thống không bị buộc chặt vào một sàn cụ thể. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Nếu thiếu cầu nối, hệ thống dễ phụ thuộc vào một sàn duy nhất và khó mở rộng khi đổi sàn hoặc API thay đổi. [📄 Nguồn](https://tiki.vn/giao-dich-su-bat-dinh-phuong-phap-dau-tu-thuc-chien-trong-moi-truong-day-ngau-nhien-cua-thi-truong-tai-chinh-p277514056.html?spid=277514057)

Cầu nối giúp tách phần logic giao dịch khỏi sự khác biệt kỹ thuật giữa các sàn: định dạng lệnh, cách nhận trạng thái, quy ước lỗi và cơ chế khớp. Khi có cầu nối chuẩn hóa, [bộ điều phối lệnh](../concepts/bo_dieu_phoi_lenh) có thể ra quyết định theo một giao diện thống nhất, còn phần “dịch” sang từng sàn nằm ở tầng cầu nối. Nhờ đó, việc thêm sàn mới hoặc thay đổi API sẽ ít ảnh hưởng tới phần còn lại của hệ thống.

Nếu cơ chế quản lý tập trung vào “cầu nối” giữa fiat và crypto (ví định danh, [sàn được cấp phép](../concepts/san_duoc_cap_phep), liên kết ngân hàng), thì phần lớn hoạt động DeFi vẫn có thể vận hành công khai trên [blockchain](../concepts/blockchain). Khi đó, cơ quan quản lý có điểm kiểm soát rõ ràng ở đầu vào/đầu ra, thay vì can thiệp sâu vào từng smart contract.

## Liên kết & Insight

Cầu nối sàn giao dịch là lớp trung gian chuẩn hóa cách hệ thống ra lệnh và nhận phản hồi từ nhiều sàn khác nhau, nhờ đó logic chiến lược không bị “dính” vào từng API. Nó kết nối với ý tưởng tách phần ra quyết định khỏi phần thực thi, tương tự cách các hệ thống giao dịch cần một cơ chế thống nhất để xử lý trạng thái và lỗi. Insight cốt lõi là: khi bạn có cầu nối, việc thêm sàn mới hoặc thay đổi kỹ thuật khớp lệnh sẽ ít làm chiến lược bị phá vỡ, giúp hệ thống mở rộng mà không phải viết lại từ đầu.

## Liên quan

* [bo\_dieu\_phoi\_lenh](../concepts/bo_dieu_phoi_lenh): cầu nối nhận quyết định cuối cùng để thực thi.
* [chi\_phi\_giao\_dich](../concepts/chi_phi_giao_dich): khác biệt thực thi giữa sàn có thể làm chi phí/khớp lệnh thay đổi.
* [truot\_gia](../concepts/truot_gia): phản hồi từ sàn giúp quan sát [trượt giá](../concepts/truot_gia) và lỗi thực thi.