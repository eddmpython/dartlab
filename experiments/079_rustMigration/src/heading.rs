//! heading 감지 + 정규화 — _detect_heading, _normalize_heading_text, _heading_key
//!
//! textStructure.py의 잎 함수들. 순수 regex 체인.

use once_cell::sync::Lazy;
use regex::Regex;

// -- regex 패턴 (Python 구현과 1:1 대응) --

static RE_ROMAN: Lazy<Regex> = Lazy::new(|| Regex::new(r"^(?:[IVXivx]+)\.\s+(.+)$").unwrap());
static RE_NUMERIC: Lazy<Regex> = Lazy::new(|| Regex::new(r"^(?:\d+)\.\s+(.+)$").unwrap());
static RE_KOREAN: Lazy<Regex> = Lazy::new(|| Regex::new(r"^(?:[가-힣])\.\s+(.+)$").unwrap());
static RE_PAREN_NUM: Lazy<Regex> = Lazy::new(|| Regex::new(r"^\((\d+)\)\s*(.+)$").unwrap());
static RE_PAREN_KOR: Lazy<Regex> = Lazy::new(|| Regex::new(r"^\(([가-힣])\)\s*(.+)$").unwrap());
static RE_CIRCLED: Lazy<Regex> = Lazy::new(|| Regex::new(r"^([①-⑳])\s*(.+)$").unwrap());
static RE_BRACKET: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^\[(.+?)\]$|^【(.+?)】$").unwrap());
static RE_SHORT_PAREN: Lazy<Regex> = Lazy::new(|| Regex::new(r"^\(([^)]+)\)$").unwrap());
static RE_HEADING_NOISE: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^(?:단위|주\d|참고|출처|비고)").unwrap());
static RE_TEMPORAL_MARKER: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^(?:\d{4}년(?:\s*\d{1,2}월)?|\d{4}[./]\d{1,2})$").unwrap());
static RE_NONWORD: Lazy<Regex> = Lazy::new(|| Regex::new(r"[^0-9A-Za-z가-힣]+").unwrap());
static RE_MULTISPACE: Lazy<Regex> = Lazy::new(|| Regex::new(r"\s+").unwrap());
static RE_TRAILING_PUNCT: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"[\s\-–—:：;,]+$").unwrap());

// mapper.py의 접두사 제거
static RE_LEAF_PREFIX: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"^\s*(?:(?:\d+|[가-힣])[.)]\s*|\(\d+\)\s*|[①-⑳]\s*)+").unwrap()
});

/// stripSectionPrefix — 잎 번호 접두사 제거
pub fn strip_section_prefix(title: &str) -> String {
    RE_LEAF_PREFIX.replace(title.trim(), "").to_string()
}

/// _normalize_heading_text — heading 라벨 정규화
pub fn normalize_heading_text(text: &str) -> String {
    let mut s = strip_section_prefix(text.trim());
    // 괄호 제거
    s = s.trim_matches(&['[', ']', '【', '】'] as &[char]).to_owned();
    // (텍스트) 짧은 괄호 → 내부
    if let Some(caps) = RE_SHORT_PAREN.captures(&s) {
        if let Some(inner) = caps.get(1) {
            s = inner.as_str().trim().to_owned();
        }
    }
    s = s.replace('ㆍ', "·");
    s = RE_MULTISPACE.replace_all(&s, " ").to_string();
    s = RE_TRAILING_PUNCT.replace(&s, "").to_string();
    s.trim().to_owned()
}

/// _heading_key — heading identity key (비단어 문자 전부 제거)
pub fn heading_key(text: &str) -> String {
    let normalized = normalize_heading_text(text);
    let no_dots = normalized.replace('·', "").replace('ㆍ', "");
    RE_NONWORD.replace_all(&no_dots, "").trim().to_owned()
}

/// _is_temporal_marker — 시점 마커 여부
pub fn is_temporal_marker(text: &str) -> bool {
    let normalized = normalize_heading_text(text);
    RE_TEMPORAL_MARKER.is_match(&normalized)
}

/// _detect_heading — 한 줄에서 heading 패턴 감지
///
/// 반환: (level, label_text, is_structural) 또는 None
pub fn detect_heading(line: &str) -> Option<(u8, String, bool)> {
    let stripped = line.trim();
    if stripped.is_empty() || stripped.starts_with('|') {
        return None;
    }
    if stripped.chars().count() > 120 {
        return None;
    }

    // 1. [텍스트] 또는 【텍스트】
    if let Some(caps) = RE_BRACKET.captures(stripped) {
        let text = caps
            .get(1)
            .or_else(|| caps.get(2))
            .map(|m| m.as_str())
            .unwrap_or("");
        let structural = !is_temporal_marker(text);
        return Some((1, text.trim().to_owned(), structural));
    }

    // 2. 로마숫자
    if let Some(caps) = RE_ROMAN.captures(stripped) {
        return Some((1, caps[1].trim().to_owned(), true));
    }

    // 3. 아라비아숫자
    if let Some(caps) = RE_NUMERIC.captures(stripped) {
        return Some((1, caps[1].trim().to_owned(), true));
    }

    // 4. 한글 (가. 나. 다.)
    if let Some(caps) = RE_KOREAN.captures(stripped) {
        return Some((2, caps[1].trim().to_owned(), true));
    }

    // 5. (숫자)
    if let Some(caps) = RE_PAREN_NUM.captures(stripped) {
        return Some((3, caps[2].trim().to_owned(), true));
    }

    // 6. (한글)
    if let Some(caps) = RE_PAREN_KOR.captures(stripped) {
        return Some((4, caps[2].trim().to_owned(), true));
    }

    // 7. 원문자 ①②③
    if let Some(caps) = RE_CIRCLED.captures(stripped) {
        return Some((4, caps[2].trim().to_owned(), true));
    }

    // 8. 짧은 괄호 (텍스트)
    if let Some(caps) = RE_SHORT_PAREN.captures(stripped) {
        let inner = caps[1].trim();
        if !inner.is_empty() && inner.chars().count() <= 48 && !RE_HEADING_NOISE.is_match(inner) {
            let structural = !is_temporal_marker(inner);
            return Some((3, inner.to_owned(), structural));
        }
    }

    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_roman() {
        let r = detect_heading("I. 회사의 개요").unwrap();
        assert_eq!(r.0, 1);
        assert_eq!(r.1, "회사의 개요");
        assert!(r.2);
    }

    #[test]
    fn test_numeric() {
        let r = detect_heading("1. 사업의 개요").unwrap();
        assert_eq!(r.0, 1);
        assert_eq!(r.1, "사업의 개요");
    }

    #[test]
    fn test_korean() {
        let r = detect_heading("가. 주요 제품").unwrap();
        assert_eq!(r.0, 2);
        assert_eq!(r.1, "주요 제품");
    }

    #[test]
    fn test_paren_num() {
        let r = detect_heading("(1) 매출액").unwrap();
        assert_eq!(r.0, 3);
        assert_eq!(r.1, "매출액");
    }

    #[test]
    fn test_circled() {
        let r = detect_heading("① 보통주").unwrap();
        assert_eq!(r.0, 4);
        assert_eq!(r.1, "보통주");
    }

    #[test]
    fn test_bracket_temporal() {
        let r = detect_heading("[2024년 12월]").unwrap();
        assert_eq!(r.0, 1);
        assert!(!r.2); // non-structural (temporal marker)
    }

    #[test]
    fn test_table_line() {
        assert!(detect_heading("| 항목 | 금액 |").is_none());
    }

    #[test]
    fn test_empty() {
        assert!(detect_heading("").is_none());
    }

    #[test]
    fn test_long_line() {
        let long = "가".repeat(121);
        assert!(detect_heading(&long).is_none());
    }

    #[test]
    fn test_heading_key() {
        assert_eq!(heading_key("가. 주요 제품 등의 현황"), "주요제품등의현황");
    }

    #[test]
    fn test_normalize() {
        assert_eq!(normalize_heading_text("1. 사업의 개요"), "사업의 개요");
        assert_eq!(normalize_heading_text("【연구개발현황】"), "연구개발현황");
    }
}
