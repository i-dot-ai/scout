# Ingesting data and analysing projects against criteria

## Overview
This is done in 3 steps:
1. Ingesting the project data
2. Ingesting criteria
3. Evaluating projects against the criteria 


## Ingesting the project data
- Takes input raw .pdf, .doc, .docx, .ppt, .pptx files and loads them into a database and vector store
- Takes input criteria from CSV files and loads them into Postgres
- These criteria are what the project will be assessed against - in the LLM flag evaluation process

### Project file processing
Recursively processes all files in a given project folder. 
- Uploads files to S3 storage
- Converts non-PDF file types (e.g. .doc, .ppt) to PDF 
- Saves file metadata to database (Postgres)
- Chunks text content of files and saves to database
- LLM-generates extra file metadata e.g. readable name and saves to database
- Embeds chunks in vector store for efficient retrieval

*Implemented in `scout/Pipeline/ingest_project_data.py`*


## Criteria loading
- Loads criteria from CSV files into the database - `criterion` table
- Criteria CSVs have columns: `#`,`Category`,`Gate`,`Question`,`Evidence`
- The `Gate` are the different reviews - and should be one of the options in `CriterionGate` (e.g. `GATE_2`)
- Supports multiple gates (e.g., `GATE_2`, `GATE_3`)

*Implemented in `scout/Pipeline/ingest_criteria.py`*


## Evaluate projects (LLM flag)
An LLM is used to evaluate the specified project against a set of pre-defined criteria for a specified review gate.

The evaluation is done using `MainEvaluator.evaluate_questions`. This evaluates against the criteria in the database using the LLM. This is done in the `answer_question` method.

### answer_question method
- Does q and a for each evidence point
- Gets an overall final answer using the answers to the earlier points
- Returns answer and chunks
- Answer is `response.choices[0].message.content` from Open AI
- Chunks is a list of `Chunk` objects read from the vector store

The results of the evaluation are saved to Postgres (`result` table).

*Implemented in `scout/Pipeline/generate_llm_flags.py`*


## Diagram of ingesting project data and criteria

```mermaid
graph TD
    A[Ingesting data] --> B[Check if S3 storage handler exists]
    B -->|Yes| C[Load criteria from CSV files]
    B -->|No| B1[Initialize new S3 storage handler]
    B1 --> C
    A --> D[Create Project object]
    D --> E[Save project files]    



    subgraph "Load Criteria"
    C1[gate_x.csv] --> C

    
    end
    DB[(PostgreSQL Database)]
    C --> DB




    subgraph "Save Project Files"
    E1[collect_file_paths]
    E2[Creates Chroma Vector Store in persist_directory]
    E3[Handle each file]
    E4[Chunk and embed file]
    end

   E4 --> CC1
    subgraph "chunk_save_embed_file"
    CC1[Check if pdf with same name exists]
    CC14[Check file type]

    CC4[docx to html via mammoth]
    CC5[html to pdf via pisa]
    CC6[pptx to pdf via LibreOffice]
    CC7[If pdf of correct name exists]
    CC8[upload_to_s3]
    CC9[Write file metadata to db / storage_handler]
    CC10[Chunk and embed file contents]
    CC11[Extract structured file info from file content using gpt3.5 and instructor. Max retries = 3 may cause errors to be missed]
    CC12[Update file in db storage_handler with new file info]
    CC13[Add chunks to vector store]
    end
CC9 --> DB
E2 --> CHROMA
   CC1 -- if not pdf --> CC14
   CC1 -- if pdf --> CC8

   CC4 --> CC5

   CC4 --> CC5
   CC5 --> CC7
   CC6 --> CC7
   CC7 --> CC8
   CC8 --> CC9
   CC9 --> CC10
   CC10 --> CC11  
   CC14 -- if docx --> CC4
   CC14 -- if pptx --> CC6
   CC11 --> CC12
   CC12 --> CC13
   CC13 --> CHROMA
   E --> E1
   E1 --> E2
   E2 --> E3
   E3 --> E4
    E4 -- for each file in file_paths --> E4


    %% Arguments for ingest_project_files
M[Parameters: project_directory_name, vector_store, storage_handler, s3_storage_handler, chunking_partition_strategy] --> A


   Note1[This function instantiates a File object and manipulates it, checking if a pdf with the same name exists after each coversion and overwriting the File object's path and type variables as needed]


   Note1 -.-> CC11


   CHROMA[(Chroma Vector Store)]

   
   classDef note fill:#ff9,stroke:#333,stroke-width:2px;
   classDef external fill:#aef,stroke:#333,stroke-width:2px;
   classDef problem fill:#f00,stroke:#333,stroke-width:2px;
   class E2 problem;
   class CC6 external;
   class Note1,Note2 note;
```

<!-- classDef default fill:#f9f,stroke:#333,stroke-width:2px; -->
