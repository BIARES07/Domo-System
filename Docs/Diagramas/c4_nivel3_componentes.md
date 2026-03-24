flowchart TB
    classDef component fill:#2ca46e,stroke:#1b6644,color:#fff;
    classDef database fill:#2e6295,stroke:#1f4264,color:#fff;

    subgraph FastAPI_Gateway ["DOMO API Gateway (FastAPI)"]
        direction TB
        AuthMid["🛡️ Middleware Auth\n(Validador de Hash)"]:::component
        ChaosMid["🎲 Middleware Caos\n(Inyector de Latencia/Errores)"]:::component
        RouterAdmin["🚦 Enrutador Admin\n(Limpio)"]:::component
        RouterIntern["🚦 Enrutador Pasante\n(Fragmentado)"]:::component
        Services["📡 Servicios Core\n(HTTPX Cliente, Mutadores)"]:::component
        BinaryPack["📦 Empaquetador Binario\n(struct Python)"]:::component
        CRUD["🗄️ Capa CRUD\n(Consultas SQL)"]:::component
    end

    DB[("SQLite")]:::database
    Redis[("Redis")]:::database

    %% Flujos internos
    AuthMid --> ChaosMid
    ChaosMid --> RouterIntern
    RouterIntern --> Services
    RouterAdmin --> Services
    Services <--> BinaryPack
    ChaosMid -.-> CRUD
    AuthMid -.-> Redis
    CRUD <--> DB