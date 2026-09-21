# Data Engineering

## Database types

A database type is a choice about how data is stored and queried. No type is best for everything. Pick the one whose strengths match the data shape and the access pattern of the workload.

**Relational (SQL) databases** (PostgreSQL, MySQL, SQL Server) store data in tables with a fixed schema. Rows in different tables are linked by keys and combined with **joins**. They give **ACID** transactions. **Atomicity** means all steps of a transaction happen or none do. **Consistency** means the data always obeys the database's rules. **Isolation** means concurrent transactions do not see each other's unfinished work. **Durability** means a committed change survives a crash. Use a relational database when the data is structured, the schema is stable, and correctness matters, as with payments, orders and inventory. Its weakness is scaling writes across many servers, because joins and transactions across machines are costly.

**NoSQL** means "not only SQL". It covers several different designs that usually relax the fixed schema or the strict transactions in return for flexibility or scale.

| Type | Data model | Typical use | Examples |
|---|---|---|---|
| **Document store** | Self-contained JSON-like documents. Fields can differ between documents. | Product catalogues, user profiles, content | MongoDB, Couchbase |
| **Key-value store** | A key maps to a value. Fast lookup by key only. | Caches, sessions, online feature serving | Redis, DynamoDB |
| **Wide-column store** | Rows grouped by a partition key, with flexible columns. Spread over many nodes. | Very high write volume, event logs, sensor data | Cassandra, HBase |
| **Graph database** | Nodes and edges. Relationships are stored directly. | Social networks, fraud rings, recommendations, knowledge graphs | Neo4j |
| **Time series database** | Timestamped points, written once. | Metrics, IoT, monitoring | InfluxDB, TimescaleDB |
| **Vector database** | Embeddings, searched by similarity. | Semantic search, RAG, recommendations | Pinecone, pgvector, Milvus |

**Document stores** keep each record in one place, so you read a whole record in one lookup and can change the shape of records without a migration. Joins across documents are weak or absent. **Key-value stores** are the simplest and fastest, often held in memory. You cannot query by the contents of the value. **Wide-column stores** need you to design tables around the queries you will run. **Graph databases** follow relationships by walking links, so "friends of friends of friends" stays fast where a relational database needs a join per step. **Time series databases** are tuned for constant timestamped appends and time-range queries, and offer downsampling and automatic deletion of old data. **Vector databases** find the stored embeddings closest to a query embedding, usually with **approximate nearest neighbour** indexes that trade a little accuracy for speed. In **retrieval-augmented generation (RAG)** they retrieve relevant text to add to a language model's prompt.

**Scaling.** **Vertical scaling** means a bigger machine. **Horizontal scaling** means more machines. Two techniques make a database work across machines. **Replication** keeps copies of the same data on several servers. It improves availability and read capacity. **Sharding** splits the data so each server holds a part. It improves write capacity and total size, but makes joins and transactions across shards harder.

**CAP theorem.** A distributed database cannot guarantee all three of **Consistency** (every read sees the latest write), **Availability** (every request gets a response) and **Partition tolerance** (it keeps working when the network splits). Partitions happen in real networks, so the real choice is between consistency and availability during a partition. A CP system refuses some requests to stay consistent. An AP system keeps answering and may return stale data. Many NoSQL systems follow **BASE**: Basically Available, Soft state, **Eventually consistent**. Eventual consistency means replicas may briefly disagree after a write but converge if writes stop. It is fine for view counts. It is not fine for account balances.

**Choosing for ML work.** Match the store to the access pattern.

- Training data for large analytical scans belongs in a warehouse, lake or lakehouse, not in an operational database.
- Online prediction that looks up the latest features by id in milliseconds needs a key-value store.
- Semantic search or RAG needs a vector store.
- Relationship-heavy problems such as fraud rings suit a graph database.
- Transactions that must be correct, such as a bank transfer, need a relational database with ACID.
- Many real systems use several stores together, each for what it does best.
