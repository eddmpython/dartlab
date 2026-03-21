"""온톨로지 빌더 - standardAccounts.json → OWL 온톨로지 변환"""

import json
from pathlib import Path

from owlready2 import *


class OntologyBuilder:
    """표준계정 온톨로지 빌더"""

    def __init__(self, dataDir: Path):
        self.dataDir = dataDir
        self.onto = None

    def build(self) -> Ontology:
        """standardAccounts.json → OWL 온톨로지 변환"""

        self.onto = get_ontology("http://dart.fss.or.kr/accounts.owl")

        with self.onto:
            self._defineClasses()
            self._defineProperties()
            self._loadAccounts()

        return self.onto

    def _defineClasses(self):
        """클래스 정의"""
        with self.onto:

            class Account(Thing):
                """계정"""

                pass

            class Industry(Thing):
                """산업 분류"""

                pass

            class StatementKind(Thing):
                """재무제표 종류"""

                pass

            class CodeType(Thing):
                """코드 타입"""

                pass

    def _defineProperties(self):
        """속성 정의"""
        with self.onto:

            class code(DataProperty, FunctionalProperty):
                """계정 코드"""

                domain = [self.onto.Account]
                range = [str]

            class korName(DataProperty):
                """한글명"""

                domain = [self.onto.Account]
                range = [str]

            class engName(DataProperty):
                """영문명"""

                domain = [self.onto.Account]
                range = [str]

            class snakeId(DataProperty, FunctionalProperty):
                """snake_case ID"""

                domain = [self.onto.Account]
                range = [str]

            class level(DataProperty, FunctionalProperty):
                """계층 레벨"""

                domain = [self.onto.Account]
                range = [int]

            class belongsToIndustry(ObjectProperty):
                """산업 분류"""

                domain = [self.onto.Account]
                range = [self.onto.Industry]

            class appearsInStatement(ObjectProperty):
                """재무제표 종류"""

                domain = [self.onto.Account]
                range = [self.onto.StatementKind]

            class hasCodeType(ObjectProperty):
                """코드 타입"""

                domain = [self.onto.Account]
                range = [self.onto.CodeType]

    def _loadAccounts(self):
        """standardAccounts.json 로드 및 온톨로지 인스턴스 생성"""

        path = self.dataDir / "standardAccounts.json"
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        metadata = data.get("_metadata", {})

        industries = {}
        for ind_code, ind_name in metadata.get("industryMapping", {}).items():
            ind_inst = self.onto.Industry(f"industry_{ind_code}")
            industries[int(ind_code)] = ind_inst

        statements = {}
        for stmt_code, stmt_name in metadata.get("statementKindMapping", {}).items():
            stmt_inst = self.onto.StatementKind(f"statement_{stmt_code}")
            statements[int(stmt_code)] = stmt_inst

        codeTypes = {}
        for code_type, type_name in metadata.get("codeTypeMapping", {}).items():
            type_inst = self.onto.CodeType(f"codetype_{code_type}")
            codeTypes[code_type] = type_inst

        for acc_data in data.get("accounts", []):
            snake_id = acc_data.get("snakeId", "")
            if not snake_id:
                continue

            industry_code = acc_data.get("industry", 0)
            stmt_kind = acc_data.get("statementKind", 0)
            code_type = acc_data.get("codeType", "M")
            code = acc_data.get("code", "")

            safe_name = f"{snake_id}_stmt{stmt_kind}_ind{industry_code}_{code_type}_{code}".replace("-", "_").replace(
                ".", "_"
            )

            try:
                acc = self.onto.Account(safe_name)
            except:
                continue

            acc.code = acc_data.get("code", "")
            acc.korName.append(acc_data.get("korName", ""))
            acc.engName.append(acc_data.get("engName", ""))
            acc.snakeId = snake_id
            acc.level = acc_data.get("level", 0)

            if industry_code in industries:
                acc.belongsToIndustry.append(industries[industry_code])

            if stmt_kind in statements:
                acc.appearsInStatement.append(statements[stmt_kind])

            if code_type in codeTypes:
                acc.hasCodeType.append(codeTypes[code_type])

    def save(self, filepath: Path):
        """온톨로지 저장"""
        if self.onto:
            self.onto.save(file=str(filepath), format="rdfxml")
