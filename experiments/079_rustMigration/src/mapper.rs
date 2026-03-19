//! Section title mapper — normalizeSectionTitle + mapSectionTitle
//!
//! mapper.py의 Rust 포팅. HashMap(182개) + regex 패턴(85개) 2단계 매핑.

use once_cell::sync::Lazy;
use regex::Regex;
use std::collections::HashMap;

use crate::heading::strip_section_prefix;

// -- regex 패턴 --
static RE_INDUSTRY_PREFIX: Lazy<Regex> = Lazy::new(|| Regex::new(r"^\([^)]*업\)").unwrap());
static RE_MULTISPACE: Lazy<Regex> = Lazy::new(|| Regex::new(r"\s+").unwrap());
static RE_TRAILING_PUNCT: Lazy<Regex> = Lazy::new(|| Regex::new(r"[-–—:：;,]+$").unwrap());
static RE_ROMAN_PREFIX: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^(?:X{0,3}(?:IX|IV|V?I{0,3}))[.\s]+").unwrap());

/// sectionMappings.json을 빌드 타임에 임베드
static MAPPINGS_JSON: &str = include_str!("sectionMappings.json");

/// 정규화된 title → topic 매핑 (182개)
static SECTION_MAPPINGS: Lazy<HashMap<String, String>> = Lazy::new(|| {
    let raw: HashMap<String, String> =
        serde_json::from_str(MAPPINGS_JSON).unwrap_or_default();
    let mut expanded = HashMap::with_capacity(raw.len());
    for (key, value) in raw {
        expanded.insert(normalize_section_title(&key), value);
    }
    expanded
});

/// _PATTERN_MAPPINGS — 85개 regex 패턴 (Python mapper.py와 1:1 대응)
static PATTERN_MAPPINGS: Lazy<Vec<(Regex, String)>> = Lazy::new(|| {
    vec![
        (r"^지적재산권보유현황\(.+\)$", "intellectualProperty"),
        (r"^연구개발실적\(.+\)$", "majorContractsAndRnd"),
        (r"^주요지적재산권현황\(상세\)$", "intellectualProperty"),
        (r"^(?:.+)?(?:주요)?연구개발실적(?:\(상세\))?$", "majorContractsAndRnd"),
        (r"^연구개발(?:실적|진행현황)-.+$", "majorContractsAndRnd"),
        (r"^핵심연구인력현황-.+$", "majorContractsAndRnd"),
        (r"^연구개발담당조직\(상세\)$", "majorContractsAndRnd"),
        (r"^연구개발실적\(상세\)-.+$", "majorContractsAndRnd"),
        (r"^(?:연구개발현황|연구개발활동)\(상세\)$", "majorContractsAndRnd"),
        (r"^수주(?:상황|현황)\(상세\)$", "salesOrder"),
        (r"^수주현황$", "salesOrder"),
        (r"^.+수주(?:상황|현황)(?:\(상세\))?$", "salesOrder"),
        (r"^사업의내용-.+수주(?:상황|현황).+$", "salesOrder"),
        (r"^\d+-\d+[,.]?사업의개요-판매조건및경로,판매전략,주요매출처\(상세\)$", "salesOrder"),
        (r"^.*경영상의주요계약(?:\(상세\)|\[상세\])?$", "majorContractsAndRnd"),
        (r"^(?:주요계약및연구개발활동|주요연구개발과제및실적)\(상세\)$", "majorContractsAndRnd"),
        (r"^(?:.+)?(?:주요)?지(?:적|식)재(?:산|선)권(?:등)?보유현황(?:\(상세\))?$", "intellectualProperty"),
        (r"^(?:.+)?(?:주요)?지(?:적|식)재(?:산|선)권(?:등)?보유현황-.+$", "intellectualProperty"),
        (r"^(?:.+)?지(?:적|식)재(?:산|선)권현황(?:\(상세\))?$", "intellectualProperty"),
        (r"^지(?:적|식)재(?:산|선)권현황-.+$", "intellectualProperty"),
        (r"^주요특허현황(?:\(상세\))?$", "intellectualProperty"),
        (r"^사업의내용-.+특허(?:보유현황|현황)$", "intellectualProperty"),
        (r"^(?:특허권보유현황\(상세\)|특허등지적재산권등록현황|지적재산권세부목록\(상세\))$", "intellectualProperty"),
        (r"^(?:주요지적재산권내용|지적재산권\(상세\)|\d+-\d+[,.]?사업의개요-지적재산권\(상세\))$", "intellectualProperty"),
        (r"^경영상의주요계약(?:\(|\[)상세(?:\)|\])$", "majorContractsAndRnd"),
        (r"^투자매매업무-장내파생상품거래현황\(상세\)$", "riskDerivative"),
        (r"^\(.+\)신용파생상품상세명세(?:\(상세\))?$", "riskDerivative"),
        (r"^(?:신용파생상품거래현황|장내파생상품거래현황)\(상세\)$", "riskDerivative"),
        (r"^(?:신용파생상품(?:상세)?명세|통화선도계약현황\(상세\))$", "riskDerivative"),
        (r"^이자율스왑의계약내용\(상세\)$", "riskDerivative"),
        (r"^\d+-\d+[,.]?사업의개요-위험관리(?:및파생거래)?\(상세\)$", "riskDerivative"),
        (r"^(?:투자매매업무-증권거래현황|투자중개업무-금융투자상품의위탁매매및수수료현황)\(상세\)$", "productService"),
        (r"^증권거래현황\(상세\)$", "productService"),
        (r"^주유소현황-.+$", "productService"),
        (r"^주요모바일요금제-.+$", "productService"),
        (r"^일임형Wrap(?:상품)?\(상세\)$", "productService"),
        (r"^투자(?:일임)?운용인력현황(?:\(상세\)|\(요약\))$", "productService"),
        (r"^(?:예금상품별개요|신탁상품별개요|외환상품및서비스(?:개요)?)$", "productService"),
        (r"^주요상품,?서비스\(\d+\).+\(상세\)$", "productService"),
        (r"^\d+-\d*\.?주요상품및서비스(?:\(상세\))?-.+(?:\(상세\))?$", "productService"),
        (r"^주요상품및서비스\(상세\)$", "productService"),
        (r"^(?:\(.+\)(?:예금업무|대출업무|e-금융서비스|방카슈랑스|신용카드상품|대출상품|예금상품|외환/수출입서비스|기타업무-외환/수출입서비스|기타업무-e-금융서비스|상품및서비스개요|신탁업무)|투자일임업무-투자운용인력현황|투자운용인력현황)\(상세\)$", "productService"),
        (r"^(?:신탁업무-재무제표|신탁업무재무제표)\(상세\)$", "financialNotes"),
        (r"^기업집단에소속된회사\(상세\)$", "affiliateGroupDetail"),
        (r"^생산설비의현황\(상세\)$", "rawMaterial"),
        (r"^(?:해외생산설비현황\(상세\)|(?:(?:\[.+?\]|\(.+?\))\s*)*물류부문영업설비현황\((?:국내|국외|해외)\))$", "rawMaterial"),
        (r"^\d+-\d+[,.]?사업의개요-생산설비의현황\(상세\)$", "rawMaterial"),
        (r"^(?:감사보고서|독립된감사인의감사보고서)$", "audit"),
        (r"^외부감사실시내용$", "audit"),
        (r"^\(첨부\)연결재무제표$", "financialNotes"),
        (r"^주석$", "financialNotes"),
        (r"^연결내부회계관리제도감사또는검토의견$", "internalControl"),
    ]
    .into_iter()
    .map(|(pat, topic)| (Regex::new(pat).unwrap(), topic.to_owned()))
    .collect()
});

/// normalizeSectionTitle — section title 정규화 (mapper.py:96-105)
pub fn normalize_section_title(title: &str) -> String {
    let mut text = strip_section_prefix(title.trim());
    text = RE_INDUSTRY_PREFIX.replace(&text, "").to_string();
    text = strip_section_prefix(&text);
    text = RE_ROMAN_PREFIX.replace(&text, "").to_string();
    text = text.replace('ㆍ', ",").replace('·', ",");
    text = RE_MULTISPACE.replace_all(&text, "").to_string();
    text = RE_TRAILING_PUNCT.replace(&text, "").to_string();
    text.trim().to_owned()
}

/// mapSectionTitle — title → topic 매핑 (HashMap + regex fallback)
pub fn map_section_title(title: &str) -> String {
    let stripped = strip_section_prefix(title);
    let normalized = normalize_section_title(&stripped);

    // 1. HashMap 조회
    if let Some(topic) = SECTION_MAPPINGS.get(&normalized) {
        return topic.clone();
    }

    // 2. regex 패턴 매칭
    for (pattern, topic) in PATTERN_MAPPINGS.iter() {
        if pattern.is_match(&normalized) {
            return topic.clone();
        }
    }

    // 3. 매핑 없으면 normalized 그대로
    normalized
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_normalize() {
        assert_eq!(normalize_section_title("1. 사업의 개요"), "사업의개요");
        assert_eq!(
            normalize_section_title("(금융업)주요 재무 현황"),
            "주요재무현황"
        );
    }

    #[test]
    fn test_map_known() {
        // sectionMappings.json에 있는 매핑
        let result = map_section_title("사업의개요");
        assert_eq!(result, "businessOverview");
    }

    #[test]
    fn test_map_pattern() {
        let result = map_section_title("수주현황");
        assert_eq!(result, "salesOrder");
    }

    #[test]
    fn test_map_unknown() {
        let result = map_section_title("존재하지않는섹션제목12345");
        // 매핑 없으면 normalized 그대로
        assert_eq!(result, "존재하지않는섹션제목12345");
    }
}
