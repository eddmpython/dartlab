use once_cell::sync::Lazy;
use regex::Regex;

/// Heading detection result: (level, label, structural)
pub type HeadingResult = (i64, String, bool);

static RE_BRACKET: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^\[(.+?)\]$|^\u{3010}(.+?)\u{3011}$").unwrap());
static RE_ROMAN: Lazy<Regex> = Lazy::new(|| Regex::new(r"^(?:[IVXivx]+)\.\s+(.+)$").unwrap());
static RE_NUMERIC: Lazy<Regex> = Lazy::new(|| Regex::new(r"^(?:\d+)\.\s+(.+)$").unwrap());
static RE_KOREAN: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^(?:[\uAC00-\uD7A3])\.\s+(.+)$").unwrap());
static RE_PAREN_NUM: Lazy<Regex> = Lazy::new(|| Regex::new(r"^\((\d+)\)\s*(.+)$").unwrap());
static RE_PAREN_KOR: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^\(([\uAC00-\uD7A3])\)\s*(.+)$").unwrap());
static RE_CIRCLED: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^([\u{2460}-\u{2473}])\s*(.+)$").unwrap());
static RE_SHORT_PAREN: Lazy<Regex> = Lazy::new(|| Regex::new(r"^\(([^)]+)\)$").unwrap());
static RE_HEADING_NOISE: Lazy<Regex> = Lazy::new(|| {
    Regex::new(
        r"^(?:단위|주\d|참고|출처|비고|계속|전문|요약|이하\s*여백|연결|별도|연결기준|별도기준|첨부|주석\s*참조)\b",
    )
    .unwrap()
});
static RE_TEMPORAL_MARKER: Lazy<Regex> = Lazy::new(|| {
    Regex::new(
        r"^(?:\d{4}년(?:\s*\d{1,2}월(?:\s*\d{1,2}일)?)?|\d{4}[./]\d{1,2}(?:[./]\d{1,2})?|제\s*\d+\s*기(?:\s*\d*\s*분기)?|(?:당|전|전전)(?:기|반기|분기)|\d{4}년\s*(?:\d분기|상반기|하반기)|FY\s*\d{4})$",
    )
    .unwrap()
});
static RE_MULTISPACE: Lazy<Regex> = Lazy::new(|| Regex::new(r"\s+").unwrap());
static RE_TRAILING_PUNCT: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"[\s\-\u{2013}\u{2014}:：;,]+$").unwrap());
static RE_NONWORD: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"[^0-9A-Za-z\uAC00-\uD7A3]+").unwrap());
static RE_INDUSTRY_PREFIX: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^\([^)]*(?:업|산업|보험|금융|지주|은행)\)\s*").unwrap());
static RE_SUFFIX_EGWANHAN: Lazy<Regex> = Lazy::new(|| Regex::new(r"에관한사항$").unwrap());

pub fn clean_line(line: &str) -> String {
    line.replace('\u{00a0}', " ").replace('\t', " ").trim_end().to_string()
}

pub fn strip_section_prefix(text: &str) -> String {
    RE_INDUSTRY_PREFIX.replace(text, "").to_string()
}

pub fn normalize_heading_text(text: &str) -> String {
    let cleaned = strip_section_prefix(text.trim());
    let cleaned = cleaned.trim_matches(|c| c == '[' || c == ']' || c == '\u{3010}' || c == '\u{3011}');
    let cleaned = if let Some(caps) = RE_SHORT_PAREN.captures(cleaned) {
        caps.get(1).map_or(cleaned.to_string(), |m| m.as_str().trim().to_string())
    } else {
        cleaned.to_string()
    };
    let cleaned = cleaned.replace('ㆍ', "·");
    let cleaned = RE_MULTISPACE.replace_all(&cleaned, " ").to_string();
    let cleaned = RE_TRAILING_PUNCT.replace(&cleaned, "").to_string();
    cleaned.trim().to_string()
}

pub fn heading_key(text: &str) -> String {
    let normalized = normalize_heading_text(text);
    let normalized = normalized.replace('·', "").replace('ㆍ', "");
    let normalized = RE_NONWORD.replace_all(&normalized, "").to_string();
    normalized.trim().to_string()
}

pub fn is_temporal_marker(text: &str) -> bool {
    let normalized = normalize_heading_text(text);
    RE_TEMPORAL_MARKER.is_match(&normalized)
}

pub fn detect_heading(line: &str) -> Option<HeadingResult> {
    let stripped = line.trim();
    if stripped.is_empty() || stripped.starts_with('|') {
        return None;
    }
    if stripped.chars().count() > 120 {
        return None;
    }

    if let Some(caps) = RE_BRACKET.captures(stripped) {
        let text = caps
            .get(1)
            .or_else(|| caps.get(2))
            .map_or("", |m| m.as_str());
        let structural = !is_temporal_marker(text);
        return Some((1, text.trim().to_string(), structural));
    }

    if let Some(caps) = RE_ROMAN.captures(stripped) {
        return Some((2, caps[1].trim().to_string(), true));
    }

    if let Some(caps) = RE_NUMERIC.captures(stripped) {
        return Some((3, caps[1].trim().to_string(), true));
    }

    if let Some(caps) = RE_KOREAN.captures(stripped) {
        return Some((4, caps[1].trim().to_string(), true));
    }

    if let Some(caps) = RE_PAREN_NUM.captures(stripped) {
        return Some((5, caps[2].trim().to_string(), true));
    }

    if let Some(caps) = RE_PAREN_KOR.captures(stripped) {
        return Some((6, caps[2].trim().to_string(), true));
    }

    if let Some(caps) = RE_CIRCLED.captures(stripped) {
        return Some((6, caps[2].trim().to_string(), true));
    }

    if let Some(caps) = RE_SHORT_PAREN.captures(stripped) {
        let inner = caps[1].trim();
        if !inner.is_empty() && inner.chars().count() <= 48 && !RE_HEADING_NOISE.is_match(inner) {
            let structural = !is_temporal_marker(inner);
            return Some((5, inner.to_string(), structural));
        }
    }

    None
}

/// Semantic segment key: apply topic-specific aliases and suffix normalization.
pub fn semantic_segment_key(
    label_key: &str,
    topic: Option<&str>,
    topic_segment_aliases: &std::collections::HashMap<String, std::collections::HashMap<String, String>>,
) -> String {
    if label_key.is_empty() || label_key.starts_with('@') {
        return label_key.to_string();
    }

    let mut key = label_key.to_string();

    if let Some(t) = topic {
        if let Some(alias_map) = topic_segment_aliases.get(t) {
            if let Some(v) = alias_map.get(&key) {
                key = v.clone();
            }
        }
    }

    key = RE_SUFFIX_EGWANHAN.replace(&key, "").to_string();
    key = key.replace("종속기업", "종속사").replace("종속회사", "종속사");

    if topic == Some("businessOverview") {
        key = key.replace("영업의개황", "영업현황");
    }
    if topic == Some("mdna") {
        key = key.replace("환율변동영향", "환율변동");
    }

    key
}
