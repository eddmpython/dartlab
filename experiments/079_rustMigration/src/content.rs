//! _splitContentBlocks — content를 text/table block으로 분해.
//!
//! 실측 318ms/종목 (Phase 1 최대 병목).
//! 순수 문자열 처리, 상태 없음.

/// content를 원문 순서대로 (blockType, blockText) 쌍으로 분해한다.
///
/// 규칙:
/// - "|"로 시작하는 줄 → table
/// - 나머지 → text
/// - 빈 줄이 table 중간에 나오면 table 블록 종료
/// - 빈 줄이 text 중간에 나오면 buffer에 유지
/// - text↔table 전환 시 이전 블록 flush
pub fn split_content_blocks(content: &str) -> Vec<(String, String)> {
    let stripped = content.trim();
    if stripped.is_empty() {
        return Vec::new();
    }
    if !stripped.contains('|') {
        return vec![("text".to_owned(), stripped.to_owned())];
    }

    let mut result: Vec<(String, String)> = Vec::new();
    let mut buffer: Vec<&str> = Vec::new();
    let mut current_kind: Option<&str> = None;

    let mut flush = |kind: Option<&str>, buf: &mut Vec<&str>, out: &mut Vec<(String, String)>| {
        if let Some(k) = kind {
            if !buf.is_empty() {
                let text = buf.join("\n");
                let trimmed = text.trim();
                if !trimmed.is_empty() {
                    out.push((k.to_owned(), trimmed.to_owned()));
                }
            }
        }
        buf.clear();
    };

    for raw in content.lines() {
        let stripped_line = raw.trim();
        if stripped_line.is_empty() {
            match current_kind {
                Some("table") => {
                    flush(current_kind, &mut buffer, &mut result);
                    current_kind = None;
                }
                Some("text") if !buffer.is_empty() => {
                    buffer.push("");
                }
                _ => {}
            }
            continue;
        }

        let next_kind = if stripped_line.starts_with('|') {
            "table"
        } else {
            "text"
        };

        if current_kind.is_none() {
            current_kind = Some(next_kind);
            buffer.push(stripped_line);
            continue;
        }

        if Some(next_kind) != current_kind {
            flush(current_kind, &mut buffer, &mut result);
            current_kind = Some(next_kind);
        }
        buffer.push(stripped_line);
    }

    flush(current_kind, &mut buffer, &mut result);
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty() {
        assert!(split_content_blocks("").is_empty());
        assert!(split_content_blocks("   ").is_empty());
    }

    #[test]
    fn test_text_only() {
        let result = split_content_blocks("hello world");
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].0, "text");
        assert_eq!(result[0].1, "hello world");
    }

    #[test]
    fn test_table_only() {
        let input = "| a | b |\n|---|---|\n| 1 | 2 |";
        let result = split_content_blocks(input);
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].0, "table");
    }

    #[test]
    fn test_mixed() {
        let input = "설명문\n\n| 항목 | 금액 |\n|---|---|\n| A | 100 |\n\n결론";
        let result = split_content_blocks(input);
        assert_eq!(result.len(), 3);
        assert_eq!(result[0].0, "text");
        assert_eq!(result[1].0, "table");
        assert_eq!(result[2].0, "text");
    }

    #[test]
    fn test_no_pipe_shortcut() {
        let input = "줄1\n줄2\n줄3";
        let result = split_content_blocks(input);
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].0, "text");
    }
}
