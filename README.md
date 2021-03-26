## Scaling Discussion
Scaling this to handle large input or changes files presents a number of challenges:  
 
**PROBLEM**: The naive implementation uses brute-force linear searches to find playlists to change.  
  

 - SOLUTION: Convert json object to a dictionary of dictionaries, such
   that each playlist is stored with its "id" property as its dictionary
   key. 
   	 - ADVANTAGE:  Lookups are O(1) instead of O(n)
   	 - DISADVANTAGE: Only scales up to the amount of memory available.  Arbitrarily large input doesn't even fit in memory, and this is only a small improvement since the lookup runs at memory speed.

  
**PROBLEM**: Arbitrarily large input files will not fit in memory.  
  

 - SOLUTION: Switch to a key-value database like MongoDB or DynamoDB
	 - ADVANTAGE:  Memory size is irrelevant, and CRUD operations are
   handled by the DB.
    - DISADVANTAGE: Now you have a DB dependency.  This may or may not be a good thing. Data model will need rethinking to work with a KV-store optimally.  For DynamoDB (and other cloud KV-stores) we need a partition key and sort key and choosing the right partition key can be tricky and requires deep knowledge of data access patterns.
  - SOLUTION: Use REDIS
	   - ADVANTAGE: Memory size is less relevant, and REDIS supports DB-like operations. 

**PROBLEM**: Arbitrarily large change files won't fit into memory

 - SOLUTION: Stream the file instead of loading the whole thing.  In
   Python, the "ijson" library provides high-level interfaces which
   yield objects from a JSON stream. 
   - ADVANTAGE: The code barely changes,
   but now we are only using enough memory to hold a single change.
   - DISADVANTAGE: This may, in fact, be even more IO-intensive if the
   file reader isn't optimized.  (ijson provides a "buf_size" option
   which can be tuned to read larger buffers, and also supports async IO
   as of Python 3.5)
- SOLUTION: Use something like AWS Kinesis or Apache Kafka + Glue to handle the change stream and the transformations.
  - ADVANTAGE: High-scale platforms like these provide nearly limitless scale-out.
    
  - DISADVANTAGE: More tools = more complexity = higher bar to entry.  More moving parts = more stuff to break.

**PROBLEM**: Assuming the in-memory store is sufficient for the input file, reading and processing any changes file via the naive approach is O(n) time complexity.

 - SOLUTION: Use a multi-threaded producer-consumer pattern.  We can
   configure ijson to allow us to control the lower-level file-like
   object read behavior.  This way, we can break up the changes file
   into chunks and issue partial reads on each chunk to fill a buffer. 
   We set up a large thread pool (more threads are better for IO-bound
   tasks), and each thread gets a chunk, and pushes the changes into a
   change queue.  A different thread pool consumes the queue and
   performs the mutations on the mixtape entities.  
   
   Depending on the isolation requirements, and whether a DBMS is used,
   we must consider locking and consistency issues.  With queued
   operations, we would need to tag each mutable operation with a
   continuation token in order to ensure read-your-write consistency. 
   Other ACID properties should be considered.  Atomicity:  many
   key-value store databases do not support multi-table transactions
   anyway, so cross-entity atomicity is easy to relax with a
   properly-thought-out data model.  Isolation: for in-memory solutions,
   not an issue.  For DBMS solutions, limited by the capabilities of the
   system.  Durability: for in-memory solutions, the cache needs to be
   checkpointed to disk periodically and transaction markers will
   increase the startup/recovery speed as well as allow better
   granularity in rollback of partial/failed mutations.
   
   We use a separate thread pool to consume the queue so that it can be
   tuned for whatever "data store" is being used.  If it is an in-memory
   store, then a number threads less-than-or-equal-to the number of
   cores is adequate.  If we are using a DBMS, then the mutations become
   IO-bound and we can run many more threads to handle IO latency.
   
   The time-complexity is still, fundamentally, O(n), but "n" is some
   quotient of row-count and thread pool size.
   
   - ADVANTAGE:  With an external DBMS, and a streaming reader for the changes file, there are virtually no limits on size of either input or output.
   - DISADVANTAGE:  Can become pretty complex - even complicated.  Also, does not preserve the time-order of the changes, since changes in the end of the file can be processed before changes in the beginning of the file.  Queues need to be configured so that they don't grow unbounded.
 
 - SOLUTION: Multi-processing model.  Each instance of the script reads 
   and processes, in one thread, a single chunk of the file.  A trivial 
   harness is written around the apply script which launches N   
   instances, one for each chunk of the input file.  This assumes that  
   mixtapes is stored in a DBMS.
   - ADVANTAGE:  Simpler than the multiprocessing solution.  Probably the easiest next step.
   - DISADVANTAGE:  Requires more runtime overhead, since each process requires its own memory.  Not as tunable as the multi-threaded producer-consumer approach.

**REALITY CHECK**:  If we are using a DBMS for the Mixtape store, then changes should be made directly.  This doesn't apply, however, if the real-world application of this architecture is something like analytics, where you need to ingest ragged or sparse log data and apply changes to a data warehouse.  ETL tools are more appropriate.