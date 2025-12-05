# 🔄 O Fluxo Git de Ouro: Guia Definitivo

Este documento define o processo padrão de desenvolvimento para garantir qualidade, segurança e organização no código. Use-o como referência rápida no dia a dia.

---

## 🚦 Guia Rápido de Decisão

| Dúvida | Ação Correta | Por quê? |
| :--- | :--- | :--- |
| **"Vou começar a trabalhar hoje"** | `git pull` na branch `develop` | Garante que você não está trabalhando em código velho. |
| **"Vou criar uma nova funcionalidade"** | `git checkout -b feature/nome` | Nunca trabalhe diretamente na `main` ou `develop`. |
| **"Fiz uma função funcionar"** | `git commit` | Salve seu progresso. Se quebrar depois, você tem um checkpoint. |
| **"Preciso ir almoçar/dormir"** | `git push` | Salva seu trabalho na nuvem. Backup é vida. |
| **"Terminei a tarefa"** | Abrir **Pull Request (PR)** | Hora de revisar e garantir que os testes passam. |
| **"O CI/CD ficou verde"** | Fazer **Merge** (no GitHub) | O código está aprovado e pronto para se juntar ao projeto. |

---

## 1. O Ciclo de Vida Passo a Passo

### 1️⃣ Preparação (Antes de Codar)
Antes de qualquer coisa, garanta que seu ambiente local está sincronizado com a realidade do projeto.

```bash
# Vá para a base segura
git checkout develop

# Baixe as novidades
git pull
```

### 2️⃣ Criação (A Branch)
Crie um universo isolado para sua tarefa. Escolha o prefixo correto:

*   `feature/` = Novas funcionalidades
*   `fix/` = Correção de bugs
*   `chore/` = Limpeza, configuração, docs

```bash
# Exemplo
git checkout -b feature/sistema-de-login
```

### 3️⃣ Desenvolvimento (O Loop Infinito)
Você codifica, testa e salva. Repita isso quantas vezes for necessário.

**Quando commitar?**
*   ✅ Criou um arquivo novo importante.
*   ✅ Fez uma função rodar sem erros.
*   ✅ Corrigiu um erro de linting.
*   ⛔ **Não commite** código quebrado que impede o projeto de rodar (a menos que seja apenas no seu PC local).

```bash
git add .
git commit -m "feat: implement basic login validation"
```

### 4️⃣ Sincronização (Pull)
Se sua feature demorar dias, a `develop` mudou. Traga essas mudanças para sua branch para evitar surpresas no final.

```bash
# 1. Volte para develop e atualize
git checkout develop
git pull

# 2. Volte para sua feature
git checkout feature/sistema-de-login

# 3. Mescle as novidades (traga o novo da develop para sua feature)
git merge develop
```

### 5️⃣ Entrega (Push & PR)
Terminou? Hora de enviar.

```bash
git push origin feature/sistema-de-login
```

**No GitHub:**
1.  Clique em **"Compare & pull request"**.
2.  Preencha o template (explique o *que* e o *por quê*).
3.  Aguarde os Checks do CI (Testes e Linting).

### 6️⃣ Finalização (Merge)
Só clique em Merge se:
1.  Todos os checks estiverem verdes (✅).
2.  Você revisou seu próprio código no PR e está satisfeito.

---

## 📝 Conventional Commits (Padrão de Mensagens)

Para manter o histórico limpo, usamos o padrão: `tipo(escopo): descrição`

| Tipo | Uso | Exemplo |
| :--- | :--- | :--- |
| `feat` | Nova funcionalidade | `feat(auth): add google oauth login` |
| `fix` | Correção de bug | `fix(api): handle timeout error correctly` |
| `docs` | Mudança na documentação | `docs: update readme usage instructions` |
| `style` | Formatação, pontos e vírgulas | `style: run ruff formatter` |
| `refactor`| Mudança de código que não altera função | `refactor: simplify user filtering logic` |
| `test` | Adição ou correção de testes | `test: add unit tests for user service` |
| `chore` | Manutenção (deps, configs) | `chore: upgrade python dependencies` |

---

## 🚨 FAQ de Emergência

**Q: Fiz um commit errado, e agora?**
A: `git reset --soft HEAD~1` (Desfaz o commit mas mantém seu código modificado para você arrumar).

**Q: O Git diz que tem "Conflito" no merge.**
A: Isso significa que você e outra pessoa mexeram na mesma linha.
1. Abra o arquivo no VS Code.
2. Procure por `<<<<<<<`.
3. Escolha qual versão é a correta (ou combine as duas).
4. Salve, `git add .` e `git commit`.

**Q: Trabalhei na `develop` sem querer!**
A: Antes de commitar:
1. `git stash` (guarda suas mudanças numa gaveta temporária).
2. `git checkout -b feature/minha-feature-certa`.
3. `git stash pop` (aplica as mudanças na branch nova).
