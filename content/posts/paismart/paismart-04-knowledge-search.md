# 模块三：知识库检索

<img src="file:///C:/Users/陈%20华%20宇/AppData/Roaming/marktext/images/2026-03-17-13-35-04-image.png" title="" alt="" data-align="right">

## 检索流程

1.获取用户的有效组织，将查询文本转化为可以用于向量检索的向量（调用embeddingClient中的方法访问api）；

2.混合检索 先用knn筛选 再用bm25关键词重排，返回搜索结果(包含chunkid，filemd5等信息)  **该搜索的语句十分复杂**

SearchResponse<EsDocument> response = esClient.search(s -> {
    s.index("knowledge_base");
    int recallK = topK * 30;

    // 1) KNN 召回
    s.knn(kn -> kn
            .field("vector")
            .queryVector(queryVector)
            .k(recallK)
            .numCandidates(recallK)
    );
    
    // 2) 必须命中关键词 + 权限过滤
    s.query(q -> q.bool(b -> b
            .must(mst -> mst.match(m -> m.field("textContent").query(query)))
            .filter(f -> f.bool(bf -> bf
                    .should(s1 -> s1.term(t -> t.field("userId").value(userDbId)))
                    .should(s2 -> s2.term(t -> t.field("public").value(true)))
                    .should(s3 -> /* orgTag should */ )
            ))
    ));
    
    // 3) 第二阶段 BM25 rescore（窗口内重排）
    s.rescore(r -> r
            .windowSize(recallK)
            .query(rq -> rq
                    .queryWeight(0.2d)         // 保留部分 KNN 分
                    .rescoreQueryWeight(1.0d)  // BM25 主导
                    .query(rqq -> rqq.match(m -> m
                            .field("textContent")
                            .query(query)
                            .operator(Operator.And)
                    ))
            )
    );
    
    s.size(topK);
    return s;

}, EsDocument.class);
