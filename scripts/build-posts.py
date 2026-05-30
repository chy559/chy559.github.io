from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "content" / "posts"
OUTPUT_FILE = ROOT / "content" / "posts-manifest.json"
VALID_CATEGORIES = {"tech", "galgame", "nongalgame"}
RAW_POST_METADATA: dict[str, dict[str, str]] = {
    "paismart/paismart-01-overview-rag.md": {
        "title": "PaiSmart 学习笔记 01：RAG 项目总览与核心链路",
        "slug": "paismart-01-overview-rag",
        "category": "tech",
        "date": "2026-05-30",
        "summary": "整理 PaiSmart 的工程启动、RAG 应用场景、Redis 使用、分片上传一致性、Kafka、ES 混合检索和 Agent 改造思路。",
        "collection": "paismart",
        "collectionTitle": "PaiSmart",
        "seriesOrder": "1",
    },
    "paismart/paismart-02-user-management.md": {
        "title": "PaiSmart 学习笔记 02：用户管理与组织权限",
        "slug": "paismart-02-user-management",
        "category": "tech",
        "date": "2026-03-15",
        "summary": "记录用户注册登录、JWT 与 Redis 缓存、组织标签管理、组织树查询和 JPA 分页等用户模块要点。",
        "collection": "paismart",
        "collectionTitle": "PaiSmart",
        "seriesOrder": "2",
    },
    "paismart/paismart-03-file-upload.md": {
        "title": "PaiSmart 学习笔记 03：文件上传、合并与异步处理",
        "slug": "paismart-03-file-upload",
        "category": "tech",
        "date": "2026-03-23",
        "summary": "拆解分片上传、Redis Bitmap、MinIO 合并、Kafka 文件处理、Tika 流式解析、向量化和删除文件流程。",
        "collection": "paismart",
        "collectionTitle": "PaiSmart",
        "seriesOrder": "3",
    },
    "paismart/paismart-04-knowledge-search.md": {
        "title": "PaiSmart 学习笔记 04：知识库混合检索",
        "slug": "paismart-04-knowledge-search",
        "category": "tech",
        "date": "2026-03-23",
        "summary": "梳理知识库检索流程、Embedding 向量化、Elasticsearch KNN 召回、BM25 重排和权限过滤。",
        "collection": "paismart",
        "collectionTitle": "PaiSmart",
        "seriesOrder": "4",
    },
    "paismart/paismart-05-chat-assistant.md": {
        "title": "PaiSmart 学习笔记 05：聊天助手与 WebSocket 流式响应",
        "slug": "paismart-05-chat-assistant",
        "category": "tech",
        "date": "2026-03-18",
        "summary": "记录聊天助手如何建立 WebSocket、读取会话历史、检索知识片段、构建 Prompt 并流式返回模型输出。",
        "collection": "paismart",
        "collectionTitle": "PaiSmart",
        "seriesOrder": "5",
    },
    "paismart/paismart-06-deployment.md": {
        "title": "PaiSmart 学习笔记 06：考辅智聊部署全流程",
        "slug": "paismart-06-deployment",
        "category": "tech",
        "date": "2026-04-16",
        "summary": "总结前后端 Docker 打包、docker-compose 编排、环境配置、Bug 修复、ECS 部署、Nginx 和 MinIO 初始化流程。",
        "collection": "paismart",
        "collectionTitle": "PaiSmart",
        "seriesOrder": "6",
    },
    "paicli/paicli-01-interview-qa.md": {
        "title": "PaiCli 学习笔记 01：MINI-CLI 项目面试问答",
        "slug": "paicli-01-interview-qa",
        "category": "tech",
        "date": "2026-05-24",
        "summary": "围绕 MINI-CLI 项目整理 ReAct、Plan-and-Execute、Multi-Agent、Memory、RAG、工具执行和面试深挖问答。",
        "collection": "paicli",
        "collectionTitle": "PaiCli",
        "seriesOrder": "1",
    },
    "paicli/paicli-02-architecture.md": {
        "title": "PaiCli 学习笔记 02：框架分层与 Agent 执行路径",
        "slug": "paicli-02-architecture",
        "category": "tech",
        "date": "2026-05-27",
        "summary": "梳理 PaiCLI 的 CLI 壳层、Agent 执行路径、LLM Client、Tool、Memory、RAG、MCP、Browser 和 Skill 系统。",
        "collection": "paicli",
        "collectionTitle": "PaiCli",
        "seriesOrder": "2",
    },
    "paicli/paicli-03-memory-rag.md": {
        "title": "PaiCli 学习笔记 03：Memory 架构与代码库 RAG",
        "slug": "paicli-03-memory-rag",
        "category": "tech",
        "date": "2026-05-30",
        "summary": "拆解短期记忆、长期记忆、上下文压缩、长期记忆检索、代码库 RAG 分片向量化和混合检索。",
        "collection": "paicli",
        "collectionTitle": "PaiCli",
        "seriesOrder": "3",
    },
    "paicli/paicli-04-plan-multi-agent.md": {
        "title": "PaiCli 学习笔记 04：Plan DAG 与 Multi-Agent 编排",
        "slug": "paicli-04-plan-multi-agent",
        "category": "tech",
        "date": "2026-05-30",
        "summary": "记录 Plan-and-Execute 的任务 DAG、Planner 规划器、Multi-Agent 主从模式、上下文传递和并行执行机制。",
        "collection": "paicli",
        "collectionTitle": "PaiCli",
        "seriesOrder": "4",
    },
    "paicli/paicli-05-hitl-tool-call.md": {
        "title": "PaiCli 学习笔记 05：HITL 人工审批与 Tool Call 链路",
        "slug": "paicli-05-hitl-tool-call",
        "category": "tech",
        "date": "2026-05-30",
        "summary": "整理 HitlToolRegistry 如何通过多态截获工具调用，以及危险工具、MCP 浏览器操作和审批闸门的执行链路。",
        "collection": "paicli",
        "collectionTitle": "PaiCli",
        "seriesOrder": "5",
    },
    "baguwen/baguwen-01-java.md": {
        "title": "八股复习 01：Java 基础",
        "slug": "baguwen-01-java",
        "category": "tech",
        "date": "2026-03-20",
        "summary": "整理 equals 与 hashCode、字符串拼接、泛型、反射、HashMap、ConcurrentHashMap 等 Java 基础高频问题。",
        "collection": "baguwen",
        "collectionTitle": "八股",
        "seriesOrder": "1",
    },
    "baguwen/baguwen-02-juc.md": {
        "title": "八股复习 02：JUC 并发基础",
        "slug": "baguwen-02-juc",
        "category": "tech",
        "date": "2026-03-29",
        "summary": "整理 CAS、死锁、synchronized、volatile、ReentrantLock、线程池等 JUC 并发基础。",
        "collection": "baguwen",
        "collectionTitle": "八股",
        "seriesOrder": "2",
    },
    "baguwen/baguwen-03-juc-practice.md": {
        "title": "八股复习 03：JUC 实战",
        "slug": "baguwen-03-juc-practice",
        "category": "tech",
        "date": "2026-04-17",
        "summary": "记录 JUC 并发实践相关题目与项目表达，用于补充线程池、锁、异步任务等实战话术。",
        "collection": "baguwen",
        "collectionTitle": "八股",
        "seriesOrder": "3",
    },
    "baguwen/baguwen-04-jvm.md": {
        "title": "八股复习 04：JVM",
        "slug": "baguwen-04-jvm",
        "category": "tech",
        "date": "2026-04-07",
        "summary": "整理 JVM 运行时内存、对象创建、垃圾回收算法、引用类型、类加载与常见调优问题。",
        "collection": "baguwen",
        "collectionTitle": "八股",
        "seriesOrder": "4",
    },
    "baguwen/baguwen-05-spring.md": {
        "title": "八股复习 05：Spring",
        "slug": "baguwen-05-spring",
        "category": "tech",
        "date": "2026-05-19",
        "summary": "整理 IoC、AOP、Bean 生命周期、单例 Bean、三级缓存循环依赖和 Spring 启动流程。",
        "collection": "baguwen",
        "collectionTitle": "八股",
        "seriesOrder": "5",
    },
    "baguwen/baguwen-06-spring-ai.md": {
        "title": "八股复习 06：Spring AI",
        "slug": "baguwen-06-spring-ai",
        "category": "tech",
        "date": "2026-05-19",
        "summary": "整理 Spring AI 相关概念和项目表达，补充 AI 应用接入、模型调用和工程化复习材料。",
        "collection": "baguwen",
        "collectionTitle": "八股",
        "seriesOrder": "6",
    },
    "baguwen/baguwen-07-mysql-redis.md": {
        "title": "八股复习 07：MySQL 与 Redis",
        "slug": "baguwen-07-mysql-redis",
        "category": "tech",
        "date": "2026-05-24",
        "summary": "整理 B+ 树、联合索引、三大日志、MVCC、Redis 跳表、持久化等数据库与缓存高频问题。",
        "collection": "baguwen",
        "collectionTitle": "八股",
        "seriesOrder": "7",
    },
    "baguwen/baguwen-08-message-queue.md": {
        "title": "八股复习 08：消息队列",
        "slug": "baguwen-08-message-queue",
        "category": "tech",
        "date": "2026-03-24",
        "summary": "整理消息队列基础、削峰解耦、可靠性、消费语义和常见面试追问。",
        "collection": "baguwen",
        "collectionTitle": "八股",
        "seriesOrder": "8",
    },
    "baguwen/baguwen-09-kafka.md": {
        "title": "八股复习 09：Kafka",
        "slug": "baguwen-09-kafka",
        "category": "tech",
        "date": "2026-03-19",
        "summary": "整理 Kafka 相关核心概念和项目表达，作为消息队列专题中的 Kafka 补充笔记。",
        "collection": "baguwen",
        "collectionTitle": "八股",
        "seriesOrder": "9",
    },
    "baguwen/baguwen-10-zookeeper.md": {
        "title": "八股复习 10：ZooKeeper",
        "slug": "baguwen-10-zookeeper",
        "category": "tech",
        "date": "2026-03-16",
        "summary": "整理 ZooKeeper 基础概念、协调能力和常见分布式系统面试点。",
        "collection": "baguwen",
        "collectionTitle": "八股",
        "seriesOrder": "10",
    },
    "baguwen/baguwen-11-network.md": {
        "title": "八股复习 11：计算机网络",
        "slug": "baguwen-11-network",
        "category": "tech",
        "date": "2026-05-24",
        "summary": "整理网页访问流程、WebSocket、HTTP/HTTPS、HTTP 版本差异、TCP 握手挥手和 TCP/UDP。",
        "collection": "baguwen",
        "collectionTitle": "八股",
        "seriesOrder": "11",
    },
    "baguwen/baguwen-12-os.md": {
        "title": "八股复习 12：操作系统",
        "slug": "baguwen-12-os",
        "category": "tech",
        "date": "2026-05-25",
        "summary": "整理操作系统相关面试知识点，覆盖进程线程、内存、IO 和系统调用等基础复习材料。",
        "collection": "baguwen",
        "collectionTitle": "八股",
        "seriesOrder": "12",
    },
    "baguwen/baguwen-13-agent.md": {
        "title": "八股复习 13：Agent",
        "slug": "baguwen-13-agent",
        "category": "tech",
        "date": "2026-05-24",
        "summary": "整理 Agent 组成、ReAct、Plan-and-Execute、Workflow 对比、Skill 机制和简单 Agent 循环。",
        "collection": "baguwen",
        "collectionTitle": "八股",
        "seriesOrder": "13",
    },
}


def parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    raw = raw.lstrip("\ufeff")
    if not raw.startswith("---\n"):
        raise ValueError("missing frontmatter start")

    end_marker = "\n---\n"
    end_index = raw.find(end_marker, 4)
    if end_index == -1:
        raise ValueError("missing frontmatter end")

    frontmatter_block = raw[4:end_index]
    body = raw[end_index + len(end_marker):].strip()
    data: dict[str, str] = {}

    for line in frontmatter_block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = stripped.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")

    return data, body


def parse_post(path: Path, raw: str) -> tuple[dict[str, str], str]:
    normalized_path = path.relative_to(POSTS_DIR).as_posix()
    raw = raw.lstrip("\ufeff")

    if raw.startswith("---\n"):
        return parse_frontmatter(raw)

    metadata = RAW_POST_METADATA.get(normalized_path)
    if not metadata:
        raise ValueError(f"{path.name} missing frontmatter start")

    return metadata, raw.strip()


def summarize_markdown(body: str, limit: int = 180) -> str:
    plain = re.sub(r"```[\s\S]*?```", " ", body)
    plain = re.sub(r"`[^`]*`", " ", plain)
    plain = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", plain)
    plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", plain)
    plain = re.sub(r"^[#>\-*+\s]+", "", plain, flags=re.MULTILINE)
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:limit].rstrip() + ("..." if len(plain) > limit else "")


def estimate_word_count(body: str) -> int:
    plain = re.sub(r"```[\s\S]*?```", " ", body)
    plain = re.sub(r"`[^`]*`", " ", plain)
    plain = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", plain)
    plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", plain)
    plain = re.sub(r"[#>*_\-\[\]\(\)!]", " ", plain)
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", plain)
    latin_words = re.findall(r"[A-Za-z0-9_]+", plain)
    return len(chinese_chars) + len(latin_words)


def collect_posts() -> list[dict[str, str | int]]:
    posts: list[dict[str, str | int]] = []

    for path in sorted(POSTS_DIR.rglob("*.md")):
        if path.name.startswith("_"):
            continue

        raw = path.read_text(encoding="utf-8")
        meta, body = parse_post(path, raw)

        required_fields = {"title", "slug", "category", "date", "summary"}
        missing = required_fields - set(meta)
        if missing:
            raise ValueError(f"{path.name} missing fields: {', '.join(sorted(missing))}")

        category = meta["category"]
        if category not in VALID_CATEGORIES:
            raise ValueError(f"{path.name} has invalid category: {category}")

        posts.append(
            {
                "title": meta["title"],
                "slug": meta["slug"],
                "category": category,
                "date": meta["date"],
                "summary": meta["summary"],
                "collection": meta.get("collection", ""),
                "collectionTitle": meta.get("collectionTitle", ""),
                "seriesOrder": int(meta.get("seriesOrder", "0") or 0),
                "path": f"./content/posts/{path.relative_to(POSTS_DIR).as_posix()}",
                "content": body,
                "excerpt": summarize_markdown(body),
                "wordCount": estimate_word_count(body),
            }
        )

    posts.sort(key=lambda post: str(post["date"]), reverse=True)
    return posts


def main() -> None:
    payload = {"posts": collect_posts()}
    OUTPUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"generated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
