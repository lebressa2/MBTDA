import time

from ..agent import Agent
from ..interfaces.base import IRunner
from ..models.data_models import AgentEvent

class ReactiveRunner(IRunner):
    """
    Runner for reactive mode with inbox and task monitoring.

    Monitors email inbox and task lists, processes events automatically.
    Use for monitoring agents that respond to external triggers.

    Inicia e para monitoring via state_machine, faz loop de polling completo,
    verifica inbox_client e task_client, detecta novos emails e tasks atrasados,
    cria AgentEvent a partir deles, ordena por prioridade e chama self.agent.process_event(event).
    Respeita self.agent.state_machine.is_monitoring(), usa poll_interval (padrão 30s),
    aceita parâmetro opcional sources: list[str] = ["inbox", "tasks"].

    Example:
        agent = Agent(text_provider=llm_client)
        runner = ReactiveRunner(sources=["inbox"], poll_interval=60)
        agent.run_with(runner)  # monitors inbox every 60s
    """

    def __init__(self, sources: list[str] = None, poll_interval: float = None):
        self.sources = sources or ["inbox", "tasks"]
        self._poll_interval = poll_interval or 30.0
        self._running = False
        self.agent = None  # será definido por set_agent_reference

    def set_agent_reference(self, agent: Agent):
        """Define a referência do agente"""
        self.agent = agent

    def start(self) -> None:
        self._running = True
        if self.agent.logger:
            self.agent.logger.info("Starting reactive monitoring...")

        try:
            while self._running:
                events_detected = []

                # Check inbox
                if 'inbox' in self.sources and self.agent.inbox_client:
                    new_emails = self.agent.inbox_client.check_new_emails()
                    for email in new_emails:
                        event = AgentEvent.from_email(email)
                        events_detected.append(event)
                        if self.agent.logger:
                            self.agent.logger.info(f"New email detected: {email.subject}")

                # Check tasks
                if 'tasks' in self.sources and self.agent.task_client:
                    self.agent.task_client.get_pending_tasks()  # Check for pending tasks
                    overdue_tasks = self.agent.task_client.get_overdue_tasks()

                    for task in overdue_tasks:
                        event = AgentEvent.from_task(task)
                        events_detected.append(event)
                        if self.agent.logger:
                            self.agent.logger.warning(f"Overdue task: {task.title}")

                # Process detected events
                for event in sorted(events_detected, key=lambda e: e.priority, reverse=True):
                    self.agent.process_event(event)

                # Wait for next poll
                if self._running:
                    time.sleep(self._poll_interval)

        except KeyboardInterrupt:
            if self.agent.logger:
                self.agent.logger.info("Monitoring stopped by user")

    def stop(self) -> None:
        self._running = False
        if self.agent.logger:
            self.agent.logger.info("Monitoring stopped")
