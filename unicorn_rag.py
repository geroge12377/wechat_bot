import os
import chromadb
from chromadb.utils import embedding_functions

class UnicornRAG:
    def __init__(self, db_path="./unicorn_memory"):
        # 4GB 内存保命：使用 PersistentClient，不占独立进程内存
        self.client = chromadb.PersistentClient(path=db_path)
        # 使用最轻量的 Embedding 模型
        self.embed_fn = embedding_functions.DefaultEmbeddingFunction()

        # 1. 静态语料库（126条）
        self.static_col = self.client.get_or_create_collection(
            name="static_corpus",
            embedding_function=self.embed_fn,
            metadata={"hnsw:space": "cosine"} # 语义相似度常用余弦距离
        )

        # 2. 动态长时记忆
        self.dynamic_col = self.client.get_or_create_collection(
            name="long_term_memory",
            embedding_function=self.embed_fn
        )

    def init_static_collection(self, list_file="unicorn.list"):
        """解析 path|speaker|lang|text 并灌库"""
        if self.static_col.count() > 0:
            print(f"[INFO] 静态语料库已存在 ({self.static_col.count()} 条)")
            return # 避免重复灌库

        ids, documents, metadatas = [], [], []
        with open(list_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                parts = line.strip().split("|")
                if len(parts) == 4:
                    path, speaker, lang, text = parts
                    ids.append(f"static_{i}")
                    documents.append(text) # 索引文本内容
                    metadatas.append({
                        "path": path,
                        "speaker": speaker,
                        "lang": lang
                    })

        self.static_col.add(ids=ids, documents=documents, metadatas=metadatas)
        print(f"[INFO] {len(ids)} 条语料已注入向量库。")

    async def query_memory(self, user_input):
        """
        实现你的需求：检索最相关3条记忆 + 1条最匹配的参考音频路径和文本
        返回：(history_context, ref_audio_path, ref_audio_text)
        """
        # 检索长时记忆（动态库）- 取前 3 条作为上下文
        mem_res = self.dynamic_col.query(
            query_texts=[user_input],
            n_results=3
        )
        history_context = " | ".join(mem_res['documents'][0]) if mem_res['documents'] and mem_res['documents'][0] else "无相关记忆"

        # 检索静态语料库 - 取最匹配的 1 条作为 SoVITS 参考音频
        static_res = self.static_col.query(
            query_texts=[user_input],
            n_results=1
        )

        ref_audio_path = ""
        ref_audio_text = ""
        if static_res['metadatas'] and static_res['metadatas'][0]:
            ref_audio_path = static_res['metadatas'][0][0]['path']
        if static_res['documents'] and static_res['documents'][0]:
            ref_audio_text = static_res['documents'][0][0]  # 获取对应的文本

        return history_context, ref_audio_path, ref_audio_text

    def save_long_term_memory(self, fact_text):
        """语义脱水后的事实存入动态库"""
        # 这里建议存入前先给个 ID（如时间戳）
        import time
        self.dynamic_col.add(
            ids=[f"mem_{int(time.time() * 1000)}"],  # 使用毫秒时间戳避免冲突
            documents=[fact_text]
        )
