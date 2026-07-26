// Generated from src/dartlab/scan/screens/*.json by landing/_scripts/buildScreens.py.
// Do not edit by hand. Python, watcher, runtime ports and public /scan consume these definitions.
import type { ScanScreenDefinition } from './scan';

export const SCAN_SCREEN_PRESETS = [
	{
		"id": "financialStabilityDrawdown",
		"version": 2,
		"schemaVersion": 1,
		"market": "kr",
		"notify": true,
		"title": "하락장 재무안전 종목",
		"tags": [
			"safety",
			"credit",
			"drawdown"
		],
		"evidence": "순현금 쿠션(현금 > 단기차입) + 이자보상배율(ICR>2) + 저부채 + 유동성 + 자본건전 = 부실회피 1차 게이트. ICR 은 복합축(이자비용+금융비용 넓은 정의). 후보는 Company/analysis 로 재검증. 절대 안전 확정 아님.",
		"spec": {
			"define": {
				"netCash": {
					"op": "sub",
					"left": "finance.account.cash_and_cash_equivalents",
					"right": "finance.account.shortterm_borrowings"
				}
			},
			"where": [
				{
					"field": "@netCash",
					"op": ">",
					"value": 0
				},
				{
					"field": "axis.debt.icr",
					"op": ">",
					"value": 2
				},
				{
					"field": "finance.ratio.debtRatio",
					"op": "<",
					"value": 80
				},
				{
					"field": "finance.ratio.currentRatio",
					"op": ">",
					"value": 150
				},
				{
					"field": "finance.account.total_stockholders_equity",
					"op": ">",
					"value": 0
				}
			],
			"select": [
				"@netCash",
				"axis.debt.icr",
				"finance.ratio.debtRatio",
				"finance.ratio.currentRatio"
			],
			"sort": {
				"field": "@netCash",
				"desc": true
			},
			"limit": 40
		}
	},
	{
		"id": "resilientCompounders",
		"version": 1,
		"schemaVersion": 1,
		"market": "kr",
		"notify": false,
		"title": "꾸준한 복리 성장주 (시계열·업종상대)",
		"tags": [
			"quality",
			"growth",
			"resilience"
		],
		"evidence": "3년 연속 흑자(min 영업이익>0) + 3년 매출 CAGR 성장 + 3년 평균 저부채 + 업종내 ROE 상위 = 하락장에도 훼손되지 않는 복리 성장 후보. 시계열(cagr·min·mean)과 업종상대(percentile)를 한 spec 으로 결합한 컴포저블 쿼리 실증. 후보는 Company/analysis 로 재검증, 절대 확정 아님.",
		"spec": {
			"define": {
				"opMin3y": {
					"op": "min",
					"field": "finance.account.operating_profit",
					"years": 3
				},
				"salesCagr3y": {
					"op": "cagr",
					"field": "finance.account.sales",
					"years": 3
				},
				"debtMean3y": {
					"op": "mean",
					"field": "finance.ratio.debtRatio",
					"years": 3
				},
				"roeIndPct": {
					"op": "percentile",
					"field": "finance.ratio.roe",
					"by": "industry"
				}
			},
			"where": [
				{
					"field": "@opMin3y",
					"op": ">",
					"value": 0
				},
				{
					"field": "@salesCagr3y",
					"op": ">",
					"value": 0.03
				},
				{
					"field": "@debtMean3y",
					"op": "<",
					"value": 120
				},
				{
					"field": "@roeIndPct",
					"op": ">",
					"value": 60
				},
				{
					"field": "finance.account.total_stockholders_equity",
					"op": ">",
					"value": 0
				}
			],
			"select": [
				"@opMin3y",
				"@salesCagr3y",
				"@debtMean3y",
				"@roeIndPct"
			],
			"sort": {
				"field": "@roeIndPct",
				"desc": true
			},
			"limit": 40
		}
	}
] as const satisfies readonly ScanScreenDefinition[];
