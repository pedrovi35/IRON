<div align="center">

<br/>

```
██╗██████╗  ██████╗ ███╗   ██╗██╗      ██████╗  ██████╗
██║██╔══██╗██╔═══██╗████╗  ██║██║     ██╔═══██╗██╔════╝
██║██████╔╝██║   ██║██╔██╗ ██║██║     ██║   ██║██║  ███╗
██║██╔══██╗██║   ██║██║╚██╗██║██║     ██║   ██║██║   ██║
██║██║  ██║╚██████╔╝██║ ╚████║███████╗╚██████╔╝╚██████╔╝
╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝  ╚═════╝
```

### ⚡ Seu diário de treino com Inteligência Artificial

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-c8ff00?style=for-the-badge)](LICENSE)

<br/>

[📱 Demo](#-screenshots) · [🚀 Instalação](#-instalação-rápida) · [⚙️ Configuração](#%EF%B8%8F-configuração) · [📖 Funcionalidades](#-funcionalidades)

<br/>

</div>

---

## 🧠 O que é o IRONLOG?

**IRONLOG** é um app de academia full-stack com **5 agentes de IA especializados**, construído para quem leva o treino a sério. Registre séries, acompanhe evolução, receba coaching personalizado e deixe a IA criar seus planos — tudo em um único lugar.

> Feito com Streamlit + Supabase + Groq (LLaMA 3.3 70B) · Interface dark mode otimizada para mobile.

---

## ✨ Funcionalidades

### 🏋️ Treino em Tempo Real
- Inicie treinos a partir de planos salvos com **reps e pesos pré-definidos**
- Marque cada série com um toque — botão **◯ Marcar / ✅ Feito**
- Timer de descanso automático com alerta sonoro ao terminar
- Ajuste peso e reps na hora se quiser, sem obrigação
- Adicione exercícios durante o treino

### 🤖 5 Agentes de IA Especializados

| Agente | Especialidade |
|--------|--------------|
| 🧠 **ATHENA** | Superinteligência fitness — analisa dados e executa ações reais no app |
| ⚡ **ZEUS** | Coach pessoal de elite — motivação, técnica e progressão de carga |
| 🔥 **HERCULES** | Especialista em força & massa — periodização, RPE e volume |
| 🌿 **APOLLO** | Nutricionista esportivo — macros, refeições e plano alimentar |
| 📊 **ORACLE** | Analista de performance — padrões, pontos fracos e tendências |

- **Coach de treino embutido** direto na tela de treino — perguntas rápidas sem sair da sessão
- Agentes com acesso real ao banco de dados (criam planos, registram metas, logam nutrição)
- Memória persistente entre conversas

### 📋 Planos de Treino
- Crie planos com qualquer combinação de exercícios
- Defina séries, reps alvo, peso e descanso por exercício
- Biblioteca com **70+ exercícios** em 6 grupos musculares
- Adicione exercícios personalizados

### 📊 Progresso & Análise
- Gráfico de evolução de carga por exercício
- 1RM estimado ao longo do tempo
- Volume semanal (kg total)
- Recordes pessoais automáticos e manuais

### 🥗 Nutrição
- Registro de refeições com kcal, proteína, carboidrato e gordura
- Totais diários e acompanhamento de macros
- Sugestões da IA baseadas no histórico

### 📏 Medidas Corporais
- Histórico de peso, % de gordura, IMC
- Medidas de peito, cintura, quadril, braços, coxas e panturrilhas

### ⏱️ Timer, 🏆 Recordes, 🧮 Calculadoras
- Timer configurável para intervalos
- PR por exercício (automático e manual)
- Calculadoras fitness (1RM, IMC, TDEE e mais)

### 🤖 Automação Inteligente (Agentes Autônomos)
- Briefing matinal diário
- Alerta após 3 dias sem treinar (gera plano de retorno)
- Relatório semanal toda segunda
- Progressão inteligente de carga
- Check de metas toda sexta
- Plano nutricional automático

---

## 🚀 Instalação Rápida

### Pré-requisitos

- Python 3.10+
- Conta no [Supabase](https://supabase.com) (gratuita)
- Chave de API no [Groq](https://console.groq.com) (gratuita)

### 1. Clone o repositório

```bash
git clone https://github.com/pedrovi35/ironlog.git
cd ironlog
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_anon_key_aqui
GROQ_API_KEY=sua_groq_api_key_aqui
GROQ_MODEL=llama-3.3-70b-versatile
```

### 4. Configure o banco de dados

No painel do Supabase, vá em **SQL Editor** e cole o conteúdo de [`schema.sql`](schema.sql). Execute.

### 5. Rode o app

```bash
streamlit run app.py
```

Acesse em `http://localhost:8501` 🎉

---

## ⚙️ Configuração

### Variáveis de Ambiente

| Variável | Descrição | Obrigatória |
|----------|-----------|-------------|
| `SUPABASE_URL` | URL do seu projeto Supabase | ✅ |
| `SUPABASE_KEY` | Chave anon do Supabase | ✅ |
| `GROQ_API_KEY` | Chave da API do Groq | ✅ |
| `GROQ_MODEL` | Modelo LLM (padrão: `llama-3.3-70b-versatile`) | ❌ |

### Stack Tecnológica

```
Frontend    →  Streamlit (Python) — dark mode, mobile first
Database    →  Supabase (PostgreSQL) — RLS habilitado
IA          →  Groq API · LLaMA 3.3 70B — ultra-rápido
Charts      →  Plotly — gráficos interativos
```

### Estrutura do Projeto

```
ironlog/
├── app.py               # Interface principal (13 páginas)
├── agents.py            # Sistema multi-agente de IA
├── automation_engine.py # Agentes autônomos e scheduler
├── database.py          # ORM Supabase
├── schema.sql           # Schema do banco de dados
├── requirements.txt     # Dependências
├── .env                 # Variáveis de ambiente (não versionar)
└── data/
    └── agent_memory.json # Memória persistente dos agentes
```

---

## 🗄️ Schema do Banco de Dados

```sql
plans            -- Planos de treino (JSONB com exercícios)
sessions         -- Histórico de treinos realizados
measurements     -- Medidas corporais ao longo do tempo
goals            -- Metas com progresso
nutrition_logs   -- Registro de refeições e macros
manual_prs       -- Recordes pessoais manuais
custom_exercises -- Exercícios personalizados do usuário
```

---

## 🤝 Contribuindo

Pull requests são bem-vindos! Para mudanças grandes, abra uma issue primeiro.

```bash
# Fork → Clone → Branch → Commit → PR
git checkout -b feature/minha-feature
git commit -m "feat: adiciona minha feature"
git push origin feature/minha-feature
```

---

## 👨‍💻 Autor

<div align="center">

<br/>

**Pedro Victor Rocha Gonçalves**

[![GitHub](https://img.shields.io/badge/GitHub-pedrovi35-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/pedrovi35)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Pedro_Victor-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/pedro-victor-rocha-gon%C3%A7alves-751b38294/)

<br/>

</div>

---

## 📄 Licença

Distribuído sob a licença MIT. Veja [`LICENSE`](LICENSE) para mais informações.

---

<div align="center">

**⚡ IRONLOG — Treine mais inteligente.**

<br/>

[![GitHub](https://img.shields.io/badge/GitHub-pedrovi35-181717?style=flat-square&logo=github)](https://github.com/pedrovi35)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Pedro_Victor-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/pedro-victor-rocha-gon%C3%A7alves-751b38294/)

</div>
