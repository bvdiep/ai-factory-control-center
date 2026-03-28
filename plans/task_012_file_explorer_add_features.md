**Nhiệm vụ**: Bổ sung tính năng cho File Explorer
**Code base**: /home/dd/work/diep/ai-factory-control-center

**Chi tiết nhiệm vụ**:
- Thêm nút Upload: Cho phép người dùng tải file lên thư mục hiện tại. Chỉ cho phép tải một số format: docx, pdf, txt, md, csv, jpg, png, jpeg, gif.
- Thêm nút Download: Cho phép tải file hoặc toàn bộ thư mục (dưới dạng zip) về máy.
    - Nếu tải từ thư mục gốc của project thì cần phải loại bỏ các thứ trong .gitignore. Có thể gọi sang bash xử lý (kết hợp với rsync).
    - Nếu cần cài thêm thư viện hoặc soft thì nhớ cập nhật vào tài liệu và README.md.
- Thêm nút Delete: Cho phép xóa file hoặc thư mục.
- Thêm nút Create Folder: Cho phép tạo thư mục mới.

- Hãy cập nhật lại tài liệu /plans/technical_document.md
