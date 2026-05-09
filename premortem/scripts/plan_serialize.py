"""JSON-сериализация Plan для CLI write/read."""
# /// script
# dependencies = ["pyyaml>=6.0"]
# ///
from __future__ import annotations
import json
from dataclasses import asdict
from datetime import date
from scripts.plan_schema import (
    Plan, Hole, HoleStatus, Importance, Confidence, Mode,
    StatusHistoryEntry, SessionRecommendation, RerunStatus, SCHEMA_VERSION,
)


def plan_to_json(p: Plan) -> str:
    def _enc(obj):
        if isinstance(obj, date):
            return obj.isoformat()
        if hasattr(obj, "value"):  # Enum
            return obj.value
        raise TypeError(f"not serializable: {type(obj).__name__}")
    return json.dumps(asdict(p), default=_enc, ensure_ascii=False, indent=2)


def plan_from_json(text: str) -> Plan:
    data = json.loads(text)
    дыры = [_hole_from_dict(h) for h in data.get("дыры", [])]
    return Plan(
        plan_name=data["plan_name"], горизонт=data["горизонт"],
        создан=date.fromisoformat(data["создан"]),
        обновлён=date.fromisoformat(data["обновлён"]),
        запусков=int(data["запусков"]),
        version=str(data.get("version", SCHEMA_VERSION)),
        контекст=data.get("контекст", {}),
        reference_class=data.get("reference_class", []),
        дыры=дыры,
        топ=data.get("топ", []),
        bias_проверка=data.get("bias_проверка"),
        reverse_премортем=data.get("reverse_премортем"),
        session_recommendation=SessionRecommendation(data["session_recommendation"]) if data.get("session_recommendation") else None,
    )


def _hole_from_dict(d: dict) -> Hole:
    история = [
        StatusHistoryEntry(
            дата=date.fromisoformat(e["дата"]),
            статус=HoleStatus(e["статус"]),
            запуск=int(e["запуск"]),
            комментарий=e.get("комментарий"),
        )
        for e in d.get("история_статуса", [])
    ]
    return Hole(
        id=d["id"], title=d["title"], углы=d["углы"],
        найдена=date.fromisoformat(d["найдена"]),
        запуск_найдена=int(d["запуск_найдена"]),
        важность=Importance(d["важность"]),
        уверенность=Confidence(d["уверенность"]),
        статус=HoleStatus(d["статус"]),
        режим=Mode(d["режим"]),
        описание=d["описание"],
        решение=d.get("решение"),
        история_статуса=история,
        причина_отказа=d.get("причина_отказа"),
        merged_from=d.get("merged_from", []),
        rerun_status=RerunStatus(d["rerun_status"]) if d.get("rerun_status") else None,
    )
