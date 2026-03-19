//! parseMajorNum — 로마숫자 장 번호 파싱
//!
//! chunker.py의 핵심 함수. 완전 안정.

use once_cell::sync::Lazy;
use regex::Regex;

static RE_MAJOR: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"^([IVXivx]+)\.\s").unwrap());

/// 로마숫자를 정수로 변환
fn roman_to_int(s: &str) -> Option<u8> {
    let upper = s.to_uppercase();
    let mut result: i32 = 0;
    let mut prev = 0;
    for ch in upper.chars().rev() {
        let val = match ch {
            'I' => 1,
            'V' => 5,
            'X' => 10,
            'L' => 50,
            'C' => 100,
            _ => return None,
        };
        if val < prev {
            result -= val;
        } else {
            result += val;
        }
        prev = val;
    }
    if result > 0 && result <= 20 {
        Some(result as u8)
    } else {
        None
    }
}

/// parseMajorNum — title에서 장 번호 추출 (I. → 1, XII. → 12)
pub fn parse_major_num(title: &str) -> Option<u8> {
    let caps = RE_MAJOR.captures(title.trim())?;
    roman_to_int(caps.get(1)?.as_str())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic() {
        assert_eq!(parse_major_num("I. 회사의 개요"), Some(1));
        assert_eq!(parse_major_num("II. 사업의 내용"), Some(2));
        assert_eq!(parse_major_num("XII. 상세표"), Some(12));
    }

    #[test]
    fn test_none() {
        assert_eq!(parse_major_num("1. 사업의 개요"), None);
        assert_eq!(parse_major_num("가. 주요 제품"), None);
        assert_eq!(parse_major_num(""), None);
    }

    #[test]
    fn test_roman_to_int() {
        assert_eq!(roman_to_int("I"), Some(1));
        assert_eq!(roman_to_int("IV"), Some(4));
        assert_eq!(roman_to_int("IX"), Some(9));
        assert_eq!(roman_to_int("XII"), Some(12));
    }
}
