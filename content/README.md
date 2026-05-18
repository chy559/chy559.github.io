# 内容目录说明

以后新增文章时，把 `md` 文件放到：

`content/posts/`

## Frontmatter 格式

每篇文章开头都需要带这一段：

```md
---
title: 文章标题
slug: article-slug
category: tech
date: 2026-05-18
summary: 用一句简短的话概括这篇文章会写什么。
---
```

## category 可选值

- `tech`
- `galgame`
- `nongalgame`

## 发布前要做的事

新增或修改文章后，运行：

```powershell
python scripts/build-posts.py
```

这个脚本会自动生成：

`content/posts-manifest.json`

前端会读取这个清单并展示文章列表。

## 模板

可以直接参考：

`content/posts/_template.md`
