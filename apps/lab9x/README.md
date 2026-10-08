# 9xLab (`lab9x`)

App lõi ERPNext v16 dùng chung cho nhiều đơn vị Việt Nam. Mỗi khách có app riêng (ví dụ `kh_aph`) phụ thuộc vào `lab9x` và chỉ chứa phần riêng của khách.

Nguyên tắc: lõi giữ **cơ chế và quy tắc dùng chung**; danh sách cụ thể của khách (kho, nhóm hàng, viết tắt công ty) nằm trong `khach/<ten>/khach.json`; luồng nghiệp vụ chỉ một khách có nằm trong app của khách đó.

Test: `python3 -m unittest discover -s lab9x/tests -t .` (chạy trong thư mục này).
