# 🤖 Agent Framework (MBTDA)

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Um framework avançado de agentes com arquitetura modular e extensível, especializado em gestão de conhecimento semântico com embedding providers configuráveis.

## 🚀 Funcionalidades Principais

### 🧠 Sistema de Embeddings Extensível

- **IEmbedderProvider Interface**: Abstração unificada para diferentes provedores de embeddings
- **GoogleEmbedderProvider**: Integração com Google Generative AI (`text-embedding-004`)
- **MockEmbedderProvider**: Simulador determinístico para desenvolvimento e testes
- **ChromaDB Integration**: Vetor store com pesquisa semântica avançada

### 🏗️ Arquitetura Modular

- **Agents**: Núcleo inteligente com contexto dinâmico
- **Components**: Módulos especializados (Memory, Tools, Workspace, etc.)
- **Clients**: Conexões com APIs externas (LLM, Email, Tasks)
- **Interfaces**: Contratos padronizados entre componentes
- **Knowledge Base**: Sistema híbrido com armazenamento semântico

## 🛠️ Instalação

### Dependências do Sistema

- Python 3.11+
- Git (para desenvolvimento)

### Instalação das Dependências

```bash
# Clone o repositório
git clone https://github.com/lebressa2/MBTDA.git
cd MBTDA

# Instale as dependências
pip install -r requirements.txt

# Ou usando uv (recomendado)
uv sync
```

### Configuração das APIs

Crie um arquivo `.env` na raiz do projeto:

```env
# API Keys para os provedores
GROQ_API_KEY=your_groq_key_here
GOOGLE_API_KEY=your_google_key_here

# Configurações padrão dos modelos
BASE_GROQ_TTS_MODEL=groq/playai-tts
BASE_GROQ_TEXT_MODEL=openai/gpt-oss-20b
BASE_GOOGLE_TTS_MODEL=google/gemini-2.5-flash-preview-tts
BASE_GOOGLE_TEXT_MODEL=google/gemini-2.5-flash
```

## 📈 Sistema de Embeddings

### 🎯 Visão Geral

O sistema de embeddings foi completamente redesenhado para oferecer máxima flexibilidade e extensibilidade:

#### **Problema Anterior**

- ChromaDB tinha embedding functions hardcoded
- Downloads de modelos externos falhavam frequentemente
- Acoplamento forte entre conhecimento e embeddings
- Dificuldade de trocar provedores

#### **Solução Implementada**

- **1. Interface IEmbedderProvider**: Contrato padronizado para qualquer provedor
- **2. Provedores Implementados**: Google e Mock com API consistente
- **3. Integration Transparente**: ChromaDB usa providers via adapter

### 🔧 Como Usar

#### **1. Uso Básico (Recomendado)**

```python
from components.knowledge import ChromaKnowledgeBase

# O sistema automaticamente usa MockEmbedderProvider
kb = ChromaKnowledgeBase()

# Store e retrieval funcionam automaticamente
doc_id = kb.store("Conteúdo inteligente sobre AI")
results = kb.retrieve("consulta semântica", top_k=5)
```

#### **2. Com Google Embeddings (Produção)**

```python
from components.knowledge import ChromaKnowledgeBase
from clients.embedder import GoogleEmbedderProvider

# Configure o provedor Google
embedder = GoogleEmbedderProvider(
    model="models/text-embedding-004"  # Quota ilimitada!
)

# Integre com ChromaKB
kb = ChromaKnowledgeBase(embedder_provider=embedder)

# Use com embeddings reais
doc_id = kb.store("Seu documento importante")
results = kb.retrieve("busca semântica avançada")
```

#### **3. Implementando seu Próprio Provider**

```python
from interfaces.base import IEmbedderProvider

class MeuEmbedderProvider(IEmbedderProvider):
    def embed_text(self, text: str) -> List[float]:
        # Sua implementação customizada
        return self.minha_logica_embedding(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(text) for text in texts]

    @property
    def dimensions(self) -> int:
        return 768  # Seu tamanho de embedding

    @property
    def model_name(self) -> str:
        return "meu-provider-personalizado"

# Use com ChromaKB normalmente
kb = ChromaKnowledgeBase(embedder_provider=MeuEmbedderProvider())
```

### 📝 Provedores Disponíveis

#### **GoogleEmbedderProvider**

- ✅ **Quota Ilimitada**: Usa `text-embedding-004` (sem restrições)
- ✅ **Dimensões**: 768 (alta qualidade)
- ✅ **API Tree**: Constrói automaticamente
- ✅ **Fallback**: Erros de quota mostrados claramente

#### **MockEmbedderProvider**

- ✅ **Sem Dependências Externas**: Funciona offline
- ✅ **Determinístico**: Mesmo texto = mesmo embedding
- ✅ **Rápido**: Ótimo para desenvolvimento
- ✅ **Configurável**: Dimensões customizáveis

### 🧪 Testando os Embeddings

#### **Teste Completo do Sistema**

```bash
# Execute o sistema de testes completo
python tests/test_complete_embedder_system.py
```

#### **Demo Interativo**

```bash
# Teste com Google API (precisa de chave válida)
python tests/test_google_embedder_demo.py

# Ou apenas:
python -m pytest tests/
```

## 📁 Estrutura do Projeto

```
MBTDA/
├── src/
│   ├── agent.py                      # 🌟 Agente principal
│   ├── interfaces/
│   │   ├── base.py                   # 🔌 Interfaces principais (IEmbedderProvider!)
│   │   └── __init__.py
│   ├── clients/
│   │   ├── embedder/                 # 🆕 NOVO!
│   │   │   ├── google_embedder.py     # Google API integration
│   │   │   ├── mock_embedder.py       # Mock para desenvolvimento
│   │   │   └── __init__.py
│   │   ├── llm/
│   │   ├── inbox/
│   │   └── tasks/
│   └── components/
│       ├── knowledge/
│       │   └── chroma_kb.py          # 🔄 Atualizado com embedders
│       ├── context/
│       ├── lifecycle/
│       └── ...
├── tests/
│   ├── test_chroma_knowledge_base.py
│   ├── test_google_embedder_demo.py  # 🆕
│   ├── test_complete_embedder_system.py  # 🆕
│   └── ...
├── docs/
├── requirements.txt
├── pyproject.toml
├── .env                      # Configurações sensíveis
└── README.md                 # Este arquivo!
```

## 🧪 Testes

### **Execução dos Testes**

```bash
# Todos os testes
python -m pytest tests/

# Testes específicos dos embeddings
python -m pytest tests/test_complete_embedder_system.py -v

# Com cobertura
python -m pytest --cov=src tests/
```

### **Estrutura dos Testes**

- **Unitários**: Testes de componentes individuais
- **Integração**: Testes de sistema completo
- **Função**: Testes de funcionalidades end-to-end

## 🔧 Desenvolvimento

### **Contribuição**

1. Fork o projeto
2. Crie uma branch feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

### **Guia de Desenvolvimento**

- Siga os padrões de código no `pyproject.toml`
- Aproveite estruturas de teste em `tests/`
- Mantenha compatibilidade com interfaces existentes
- Documente novas funcionalidades

## 📚 Arquitetura Detalhada

### **IEmbedderProvider Interface**

```python
class IEmbedderProvider(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Gera embedding para texto único"""

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para múltiplos textos"""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Retorna dimensões do embedding"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Nome identificador do modelo"""
```

### **ChromaKnowledgeBase Integration**

- Aceita `embedder_provider` opcional no constructor
- Auto-fallback para `MockEmbedderProvider` padrão
- Adaptador `CustomEmbeddingFunction` para ChromaDB
- Método `get_embedding_model_info()` para diagnóstico

## 🚦 Limitações Conhecidas

### **Google API**

- **Quota Gratuita**: Algumas contas podem ter limites temporários
- **Modelo Recomendado**: Sempre use `text-embedding-004` (ilimitado)

### **ChromaDB**

- **Performance**: Considere o tamanho da coleção para muitos documentos
- **Indexes**: Reindexing necessário ao trocar modelos de embedding

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, leia o guia de desenvolvimento e envie suas melhorias através de issues e pull requests.

---

**Desenvolvido com ❤️ para agentes inteligentes e sistemas de conhecimento avançado.**
