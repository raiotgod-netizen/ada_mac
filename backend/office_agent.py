from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence
import importlib
import subprocess
import sys


class OfficeAgent:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_name(self, filename: str, default_stem: str, extension: str) -> Path:
        raw = (filename or "").strip() or f"{default_stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        path = Path(raw)
        stem = path.stem or default_stem
        safe_stem = "".join(c for c in stem if c.isalnum() or c in ("-", "_", " ")).strip().replace(" ", "_") or default_stem
        return self.base_dir / f"{safe_stem}{extension}"

    def _ensure_package(self, module_name: str, pip_name: str):
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", pip_name], check=True, capture_output=True, text=True, timeout=180)
                return importlib.import_module(module_name)
            except Exception as e:
                raise RuntimeError(f"Falta la dependencia '{pip_name}' y no pude instalarla automáticamente: {e}") from e

    def _normalize_rows(self, rows: Sequence[Sequence[str]] | None) -> list[list[str]]:
        normalized = []
        for row in rows or []:
            if isinstance(row, (list, tuple)):
                normalized.append([str(value) if value is not None else "" for value in row])
            else:
                normalized.append([str(row)])
        return normalized

    def _normalize_slides(self, slides: Iterable[dict] | None) -> list[dict]:
        normalized = []
        for item in slides or []:
            if isinstance(item, dict):
                normalized.append(item)
            elif isinstance(item, str):
                normalized.append({"title": item, "bullets": []})
        return normalized

    def create_word_document(self, title: str, body: str, filename: str | None = None) -> dict:
        try:
            docx = self._ensure_package("docx", "python-docx")
            output = self._safe_name(filename or title, "documento", ".docx")
            doc = docx.Document()
            if title:
                doc.add_heading(title, level=1)
            content = (body or "").strip() or "Documento generado por ADA."
            for paragraph in content.split("\n\n"):
                paragraph = paragraph.strip()
                if paragraph:
                    doc.add_paragraph(paragraph)
            doc.save(output)
            return {"ok": True, "path": str(output), "result": f"Documento Word guardado en {output}"}
        except Exception as e:
            return {"ok": False, "result": f"Error generando Word: {e}"}

    def create_excel_workbook(self, title: str, rows: Sequence[Sequence[str]] | None = None, filename: str | None = None, sheet_name: str = "Hoja1") -> dict:
        try:
            openpyxl = self._ensure_package("openpyxl", "openpyxl")
            output = self._safe_name(filename or title, "hoja_calculo", ".xlsx")
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = (sheet_name or "Hoja1")[:31]
            if title:
                ws["A1"] = title
            start_row = 2 if title else 1
            normalized_rows = self._normalize_rows(rows)
            if not normalized_rows:
                normalized_rows = [["Documento generado por ADA"]]
            for row_index, row in enumerate(normalized_rows, start=start_row):
                for col_index, value in enumerate(row, start=1):
                    ws.cell(row=row_index, column=col_index, value=value)
            wb.save(output)
            return {"ok": True, "path": str(output), "result": f"Archivo Excel guardado en {output}"}
        except Exception as e:
            return {"ok": False, "result": f"Error generando Excel: {e}"}

    def create_powerpoint_presentation(self, title: str, slides: Iterable[dict] | None = None, filename: str | None = None) -> dict:
        try:
            pptx = self._ensure_package("pptx", "python-pptx")
            output = self._safe_name(filename or title, "presentacion", ".pptx")
            prs = pptx.Presentation()

            title_slide = prs.slides.add_slide(prs.slide_layouts[0])
            title_slide.shapes.title.text = title or "Presentación"
            subtitle = title_slide.placeholders[1] if len(title_slide.placeholders) > 1 else None
            if subtitle:
                subtitle.text = "Creado por ADA"

            normalized_slides = self._normalize_slides(slides)
            if not normalized_slides:
                normalized_slides = [{"title": "Resumen", "bullets": ["Presentación generada por ADA"]}]

            for slide_data in normalized_slides:
                slide = prs.slides.add_slide(prs.slide_layouts[1])
                slide.shapes.title.text = str(slide_data.get("title") or "Diapositiva")
                body = slide.placeholders[1] if len(slide.placeholders) > 1 else None
                if body:
                    text_frame = body.text_frame
                    text_frame.clear()
                    bullets = slide_data.get("bullets") or []
                    if isinstance(bullets, str):
                        bullets = [line.strip() for line in bullets.splitlines() if line.strip()]
                    bullets = bullets or ["Contenido generado por ADA"]
                    for idx, bullet in enumerate(bullets):
                        if idx == 0:
                            text_frame.text = str(bullet)
                        else:
                            text_frame.add_paragraph().text = str(bullet)

            prs.save(output)
            return {"ok": True, "path": str(output), "result": f"Presentación PowerPoint guardada en {output}"}
        except Exception as e:
            return {"ok": False, "result": f"Error generando PowerPoint: {e}"}
