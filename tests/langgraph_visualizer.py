"""Utility for exporting the LangGraph workflow to a PNG image."""

import os
import sys
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.workflows.main_workflow import create_main_workflow
from src.services.database_analytics_service import DatabaseAnalyticsService
from src.services.prompt_service import PromptService


class DummyLLM:
    """Minimal LLM stub used only for graph construction."""

    async def generate(self, prompt: str, **kwargs) -> str:
        return "{}"

    async def generate_with_history(self, messages, **kwargs) -> str:
        return "ok"


class LangGraphVisualizer:
    """Builds and exports the compiled LangGraph workflow."""

    def __init__(
        self,
        output_path: Optional[str] = None,
        fontname: Optional[str] = None,
    ):
        self.output_path = Path(output_path or "tests/langgraph_workflow.png").resolve()
        self.fontname = fontname or "Arial"
        self.workflow = None

    def build_workflow(self):
        self.workflow = create_main_workflow(
            llm_service=DummyLLM(),
            prompt_service=PromptService(),
            db_service=DatabaseAnalyticsService(db_url=None),
        )
        return self.workflow

    def print_graph_summary(self):
        if self.workflow is None:
            raise RuntimeError("Workflow not built. Call build_workflow() first.")

        graph = self.workflow.get_graph()
        print("LangGraph workflow summary")
        print("Nodes:")
        for node in graph.nodes.values():
            print(f"  - {node.id}")

        print("Edges:")
        for edge in graph.edges:
            print(f"  - {edge.source} -> {edge.target}")

    def save_png(self):
        if self.workflow is None:
            raise RuntimeError("Workflow not built. Call build_workflow() first.")

        graph = self.workflow.get_graph()
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            graph.draw_png(str(self.output_path), fontname=self.fontname)
            print(f"Saved LangGraph workflow image to: {self.output_path}")
            return
        except Exception as exc:
            print("pygraphviz render failed, trying Mermaid fallback...", exc)

        try:
            graph.draw_mermaid_png(output_file_path=str(self.output_path))
            print(f"Saved LangGraph workflow image via Mermaid fallback to: {self.output_path}")
        except Exception as exc:
            raise RuntimeError(
                "Failed to render LangGraph image with both pygraphviz and Mermaid fallback. "
                "Install pygraphviz or ensure Mermaid API access is available."
            ) from exc


def main():
    visualizer = LangGraphVisualizer(output_path="tests/langgraph_workflow.png")
    visualizer.build_workflow()
    visualizer.print_graph_summary()
    visualizer.save_png()


if __name__ == "__main__":
    main()
