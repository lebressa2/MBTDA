# 🚀 Plano de Implementação: Integração RACI com Layered Workspace

**Data**: 11/12/2025
**Etapa**: Toolcalling com RACI e Melhorias no Workspace
**Prioridade**: Alta

---

## 📋 Visão Geral

Esta etapa foca na integração completa entre o RACIToolManager e o LayeredWorkspaceManager, garantindo que todas as execuções de ferramentas aconteçam no Layer 3 (INTERPRETER) para maior segurança e isolamento.

---

## 🎯 Objetivos Principais

1. **Segurança**: Garantir que todas as operações de código executem no Layer 3 (INTERPRETER)
2. **Compatibilidade**: Manter a API existente do RACIToolManager sem quebras
3. **Auditoria**: Melhorar o rastreamento de em qual camada cada operação ocorreu
4. **Promoção de Arquivos**: Sistema para mover arquivos do INTERPRETER para PROJECT após validação

---

## 🔧 Decisões de Design

### 1. Auto-Mode (Futuro)
- **Abordagem**: Implementar ambos os enfoques (LLM dedicado vs mesmo LLM com prompt especializado)
- **Testes**: Comparar performance objetivamente antes de decidir
- **Prioridade**: Após conclusão do toolcalling RACI

### 2. Layered Workspace
- **Sistema de Promoção**: Sim, adicionar capacidade de mover arquivos entre camadas
- **Segurança**: Validar todos os paths para prevenir path traversal
- **Auditoria**: Rastrear todas as operações com detalhes de camada

### 3. Integração RACI
- **Execução de Código**: Sempre forçar Layer 3 (INTERPRETER)
- **Operações de Arquivo**: Validar camadas e prevenir escapes
- **Compatibilidade**: Manter interface existente do RACIToolManager

---

## 📁 Arquitetura Proposta

### Modificações no LayeredWorkspaceManager

```python
# Novo método de segurança
def enforce_layer_3_operation(self, operation_name: str, path: str) -> Path:
    """Garantir que operações perigosas aconteçam no Layer 3"""
    if path.startswith('/') or '..' in path:
        raise SecurityError(f"Path traversal attempt in {operation_name}")
    return self._resolve_path(path, WorkspaceLayer.INTERPRETER)

# Auditoria melhorada
def _log_action(self, action: str, path: str, success: bool, layer: WorkspaceLayer | None = None, operation_type: str = "default") -> None:
    """Log com mais detalhes incluindo tipo de operação"""
    self._audit_log.append({
        "action": action,
        "path": path,
        "layer": (layer or self._default_layer).value,
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "operation_type": operation_type,
        "security_level": "high" if layer == WorkspaceLayer.INTERPRETER else "medium"
    })

# Sistema de promoção
def promote_file_to_project(self, interpreter_path: str, project_path: str) -> bool:
    """Move file from INTERPRETER to PROJECT layer after validation"""
    try:
        source = self._resolve_path(interpreter_path, WorkspaceLayer.INTERPRETER)
        dest = self._resolve_path(project_path, WorkspaceLayer.PROJECT)

        if not source.exists():
            return False

        shutil.copy2(source, dest)

        self._log_action(
            "promote_file",
            f"{interpreter_path} -> {project_path}",
            True,
            WorkspaceLayer.PROJECT,
            "promotion"
        )

        return True
    except Exception as e:
        self._log_action(
            "promote_file",
            f"{interpreter_path} -> {project_path}",
            False,
            WorkspaceLayer.PROJECT,
            "promotion"
        )
        return False
```

### Modificações no RACIToolManager

```python
def _execute_code(self, code: str) -> dict[str, Any]:
    """Execute Python code in the interpreter layer (Layer 3)"""
    if not code:
        return {"success": False, "error": "No code provided"}

    if len(code) > self._max_code_length:
        return {
            "success": False,
            "error": f"Code exceeds maximum length of {self._max_code_length} characters"
        }

    # Garantir execução no Layer 3
    result = self._interpreter.execute(code, layer=WorkspaceLayer.INTERPRETER)
    return result.to_dict()

def _read_file(self, path: str) -> dict[str, Any]:
    """Read a file with layer validation"""
    if not path:
        return {"success": False, "error": "No path provided"}

    # Validar path para prevenir escapes
    safe_path = self._workspace.enforce_layer_3_operation("read_file", path)
    content = self._workspace.read_file(str(safe_path))

    if content is None:
        return {"success": False, "error": f"File not found: {path}"}

    return {
        "success": True,
        "path": path,
        "content": content,
        "length": len(content),
        "layer": "INTERPRETER"
    }
```

---

## 📅 Plano de Implementação

### Fase 1: Melhorias no LayeredWorkspace (1 dia)
- [ ] Adicionar métodos de segurança para prevenir path traversal
- [ ] Melhorar sistema de auditoria com mais detalhes sobre camadas
- [ ] Implementar sistema de promoção entre camadas (INTERPRETER -> PROJECT)
- [ ] Criar testes unitários para validação de camadas no workspace

### Fase 2: Integração RACI com LayeredWorkspace (1 dia)
- [ ] Modificar RACIToolManager para usar métodos seguros do workspace
- [ ] Garantir que execute_code sempre use Layer 3 (INTERPRETER)
- [ ] Adicionar validação de camadas para read/write operations
- [ ] Atualizar métodos de auditoria para incluir informações de camada

### Fase 3: Testes de Integração (1 dia)
- [ ] Criar testes que validem o isolamento de camadas
- [ ] Testar cenários de promoção de arquivos
- [ ] Validar que operações perigosas são bloqueadas
- [ ] Testar performance e segurança do sistema

---

## 🔍 Testes Propostos

### Testes Unitários para LayeredWorkspace
```python
def test_layer_3_enforcement():
    workspace = LayeredWorkspaceManager("/tmp/test")
    # Deve lançar exceção para paths com ..
    with pytest.raises(SecurityError):
        workspace.enforce_layer_3_operation("test", "../../etc/passwd")

def test_promotion_system():
    workspace = LayeredWorkspaceManager("/tmp/test")
    # Criar arquivo no INTERPRETER
    workspace.create_file("test.py", "print('hello')", WorkspaceLayer.INTERPRETER)
    # Promover para PROJECT
    result = workspace.promote_file_to_project("test.py", "output.py")
    assert result == True
    assert workspace.file_exists("output.py", WorkspaceLayer.PROJECT)
```

### Testes de Integração RACI
```python
def test_raci_layer_3_execution():
    workspace = LayeredWorkspaceManager("/tmp/test")
    interpreter = SandboxInterpreter(workspace)
    tools = RACIToolManager(interpreter, workspace)

    # Executar código deve acontecer no Layer 3
    result = tools._execute_code("1 + 1")
    assert result["layer"] == "INTERPRETER"

    # Operações de arquivo devem ser validadas
    with pytest.raises(SecurityError):
        tools._read_file("../../etc/passwd")
```

---

## 📈 Métricas de Sucesso

1. **100% das execuções de código acontecem no Layer 3**
2. **0% de operações perigosas (path traversal) conseguem escapar**
3. **Sistema de promoção funciona corretamente para 100% dos casos de teste**
4. **Auditoria registra corretamente todas as operações com informações de camada**
5. **Performance não é impactada negativamente pelas validações adicionais**

---

## 🎯 Próximos Passos

1. **Implementar melhorias no LayeredWorkspaceManager**
2. **Modificar RACIToolManager para integração segura**
3. **Criar testes abrangentes para validar a implementação**
4. **Documentar a nova funcionalidade e criar exemplos**
5. **Iniciar implementação do Auto-Mode após conclusão**

---

## 📝 Notas Adicionais

- Manter compatibilidade com versões anteriores
- Garantir que todas as mudanças sejam cobertas por testes
- Documentar qualquer mudança na API
- Criar exemplos de uso para os novos recursos

**Responsável**: Equipe de Desenvolvimento
**Status**: Planejamento Concluído
**Próxima Revisão**: 12/12/2025
