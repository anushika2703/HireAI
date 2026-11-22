"""Skill taxonomy: canonical name -> lowercase aliases. Extend freely."""

SKILLS: dict[str, list[str]] = {
    # languages
    "Python": ["python", "python3"],
    "Java": ["java"],
    "JavaScript": ["javascript", "es6"],
    "TypeScript": ["typescript"],
    "Go": ["golang"],
    "C++": ["c++"],
    "C#": ["c#"],
    "SQL": ["sql", "pl/sql"],
    # frameworks
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "Django": ["django"],
    "Spring Boot": ["spring boot", "springboot"],
    "Node.js": ["node.js", "nodejs", "node js", "express.js"],
    "React": ["react", "react.js", "reactjs", "react native"],
    "Next.js": ["next.js", "nextjs"],
    "HTML/CSS": ["html", "css", "html5", "css3", "tailwind"],
    # data stores
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch", "elastic search", "opensearch"],
    # architecture
    "REST APIs": ["restful", "rest api", "rest apis"],
    "GraphQL": ["graphql"],
    "Microservices": ["microservices", "microservice"],
    "System Design": ["system design", "distributed systems", "scalable systems"],
    "Kafka": ["kafka"],
    "RabbitMQ": ["rabbitmq"],
    # cloud / devops
    "AWS": ["aws", "amazon web services", "ec2"],
    "GCP": ["gcp", "google cloud"],
    "Azure": ["azure"],
    "Docker": ["docker", "containerised", "containerized"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Terraform": ["terraform"],
    "CI/CD": ["ci/cd", "cicd", "jenkins", "github actions", "gitlab ci"],
    "Linux": ["linux"],
    "Git": ["git"],
    "Monitoring": ["prometheus", "grafana", "datadog", "observability"],
    # data / ML
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning", "neural networks"],
    "PyTorch": ["pytorch"],
    "TensorFlow": ["tensorflow"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "NLP": ["nlp", "natural language processing"],
    "LLMs": ["llm", "llms", "large language models"],
    "LangChain": ["langchain"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Spark": ["spark", "pyspark"],
    "Airflow": ["airflow"],
    "Data Pipelines": ["data pipelines", "data pipeline", "etl", "data engineering"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"],
    # practices
    "Testing": ["unit testing", "pytest", "junit", "test automation", "unit tests"],
    "Agile": ["agile", "scrum"],
}

# Short, ambiguous terms matched only in this exact casing ("REST", not "the rest of").
CASE_SENSITIVE: dict[str, list[str]] = {"REST APIs": ["REST"], "LLMs": ["RAG"]}
