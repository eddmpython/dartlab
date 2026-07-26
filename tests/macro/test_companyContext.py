from __future__ import annotations


class FakeCompany:
    stockCode = "005930"

    def industry(self):
        return {
            "industry": "semiconductor",
            "stage": "fab",
            "stageName": "전공정",
        }

    def analysis(self, axis):
        assert axis == "종합평가"
        return {
            "product": {
                "drivers": [
                    {
                        "id": "debtRatio",
                        "label": "부채비율",
                        "value": 35.0,
                        "unit": "%",
                        "period": "2024",
                        "direction": "positive",
                    },
                    {
                        "id": "interestCoverage",
                        "label": "이자보상배율",
                        "value": 18.0,
                        "unit": "배",
                        "period": "2024",
                        "direction": "positive",
                    },
                ]
            }
        }


def testBuildMacroCompanyContextUsesExistingLensProducts() -> None:
    from dartlab.synth.macroCompanyContext import buildMacroCompanyContext

    result = buildMacroCompanyContext(FakeCompany())

    assert result["stockCode"] == "005930"
    assert result["sectorKey"] == "semiconductor"
    assert {row["label"] for row in result["companyEvidence"]} >= {
        "부채비율",
        "이자보상배율",
        "가치사슬 위치",
    }
    assert result["contextGaps"] == []
