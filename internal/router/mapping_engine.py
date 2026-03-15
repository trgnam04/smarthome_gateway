# internal/router/mapping_engine.py

import json
from typing import List, Dict
from internal.models import Event, MappingRule, ActionDef, TriggerDef, Intent

class MappingEngine:
    """
    Biên dịch các MappingRule thành dạng Hash Map (Dictionary) 
    để tra cứu Event -> Action với tốc độ O(1).
    """
    def __init__(self):
        # Cấu trúc: {"source_device:event_name": [ActionDef_1, ActionDef_2]}
        self._rules_map: Dict[str, List[ActionDef]] = {}

    def load_rules(self, rules: List[MappingRule]):
        self._rules_map.clear()
        for rule in rules:
            trigger_key = f"{rule.trigger.source_device}:{rule.trigger.event_name}"
            if trigger_key not in self._rules_map:
                self._rules_map[trigger_key] = []
            self._rules_map[trigger_key].append(rule.action)
        print(f"[Mapping Engine] Đã tải thành công {len(rules)} luật định tuyến vào RAM.")

    def load_from_json_file(self, filepath: str):
        """Đọc kịch bản Mapping từ file JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"[Mapping Engine] Lỗi đọc file {filepath}: {e}")
            return

        rules = []
        for item in data.get("mappings", []):
            try:
                trigger = TriggerDef(**item["trigger"])
                action = ActionDef(
                    target_device=item["action"]["target_device"],
                    target_endpoint=item["action"]["target_endpoint"],
                    intent=Intent(item["action"]["intent"])
                )
                rule = MappingRule(rule_id=item["rule_id"], trigger=trigger, action=action)
                rules.append(rule)
            except KeyError as e:
                print(f"[Mapping Engine] Bỏ qua luật '{item.get('rule_id')}': Thiếu trường {e}")
                
        self.load_rules(rules)

    def get_actions_for_event(self, event: Event) -> List[ActionDef]:
        trigger_key = f"{event.source_device}:{event.event_name}"
        return self._rules_map.get(trigger_key, [])