# Turtle Trading Wiki — Crawled Knowledge Graph

Bộ dữ liệu crawl từ [wiki.turtletrading.vn](https://wiki.turtletrading.vn) để dùng làm **mỏ neo tri thức (knowledge anchor)** cho các hệ thống khác.

## Thống kê

| Metric | Value |
|--------|-------|
| Tổng pages | 696 |
| Concepts | 683 |
| Hubs | 12 |
| Index | 1 |
| Edges (liên kết nội bộ) | 4,303 |
| Crawl date | 2026-04-21 |
| Failures | 0 |

## Cấu trúc thư mục

```
crawl-wiki/
├── concepts/           # 683 khái niệm (.md)
├── hubs/               # 12 trang điều hướng lĩnh vực (.md)
├── index.md            # Trang chủ
├── graph.json          # Knowledge graph: nodes + edges
└── manifest.json       # Danh sách URL và trạng thái crawl
```

## Định dạng file Markdown

Mỗi file có YAML frontmatter:

```yaml
---
title: <tiêu đề>
source_url: <URL gốc>
tags: [tag1, tag2]
backlinks:
  - text: <tên trang liên kết ngược>
    href: <đường dẫn>
related_count: <số liên kết nội bộ>
crawled_at: <ISO timestamp>
---
```

Nội dung markdown giữ nguyên:
- Heading structure
- Internal links dạng `[text](../concepts/slug)`
- Source links (📄 Nguồn) trỏ về bài blog gốc

## Cách dùng làm mỏ neo

### 1. RAG / Vector DB
- Đọc tất cả `.md` trong `concepts/` và `hubs/`
- Chunk theo heading hoặc paragraph
- Embed và lưu vào vector store
- Metadata gồm `source_url`, `tags`, `title`

### 2. Knowledge Graph
- Load `graph.json`
- Nodes có `id`, `title`, `type` (concept|hub), `tags`
- Edges có `source`, `target`, `label`
- Dùng để traversal, recommend related concepts, hoặc visualize

### 3. Fine-tuning / Prompt context
- Gom các concept cùng hub thành context windows
- Dùng backlinks để tạo "conversation memory" về chủ đề

## Lưu ý

- Nội dung thuộc về tác giả gốc tại wiki.turtletrading.vn
- Dùng cho mục đích cá nhân / nội bộ, tôn trọng bản quyền
- Links nội bộ dùng relative path (`../concepts/...`) — cần resolve nếu serve qua HTTP
