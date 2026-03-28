#5

**Nhiệm vụ**: Hiển thị màn hình execution khi user thực hiện nhiệm vụ

**Code base**: /home/dd/work/diep/ai-factory-control-center

**Chi tiết nhiệm vụ**:
- Làm một trang Execution, trang này không có menu, trang này được mở ra khi user click vào nút Execute một phase.
- Rà soát các chỗ nhấn nút Execute để gắn link sang đây (trước đây đang để alert Under construction)
- Nội dung của trang gồm 3 phần:
    - Phần trên (card): project name, workspace (của project của phase), phase status.
    - Phần tiếp theo (card):
        - Mission
        - Input deliverables: mục này ghi "TODO"
    - Phần dưới: Một form gồm (lần lượt từ trên xuống)
        - Prompt (text area full width)
        - Nút Execute. Trước mắt lên alert Under construction
        - Ô hiển thị log giao diện kiểu console.
- Cập nhật tài liệu /plans/technical_document.md