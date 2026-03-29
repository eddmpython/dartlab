use std::collections::HashMap;

use blake2::{Blake2b, Digest};
use blake2::digest::consts::U8;

use crate::heading;

#[derive(Clone, Debug)]
pub struct StackEntry {
    pub level: i64,
    pub label: String,
    pub key: String,
    pub semantic_key: String,
}

#[derive(Debug)]
pub struct TextNode {
    pub text_node_type: String,
    pub text_structural: bool,
    pub text_level: i64,
    pub text_path: Option<String>,
    pub text_path_key: Option<String>,
    pub text_parent_path_key: Option<String>,
    pub text_semantic_path_key: Option<String>,
    pub text_semantic_parent_path_key: Option<String>,
    pub segment_order: i64,
    pub segment_key_base: String,
    pub text: String,
}

static TOPIC_SEGMENT_ALIASES: once_cell::sync::Lazy<
    HashMap<String, HashMap<String, String>>,
> = once_cell::sync::Lazy::new(|| {
    let mut m: HashMap<String, HashMap<String, String>> = HashMap::new();

    let mut co = HashMap::new();
    co.insert("연결대상종속기업개황".into(), "연결대상종속사현황".into());
    co.insert("연결대상종속회사개황".into(), "연결대상종속사현황".into());
    co.insert("연결대상종���기업현황".into(), "연��대상종속사현황".into());
    co.insert("연결대상종속회사현황".into(), "연결대상종속사현황".into());
    co.insert("��결대상종속회사현황요약".into(), "연결대상종속사현황".into());
    co.insert("연결대상종���회사개황요약".into(), "연결���상종속사현���".into());
    co.insert("연결대상종속기업개황요약".into(), "연결대상종속사현황".into());
    co.insert("연결대���종속기업현황요약".into(), "연결대상종속사현황".into());
    co.insert("연결���상회사의변동내용".into(), "연결대상변동내용".into());
    co.insert("연결대상회사의변동현황".into(), "연결대상변동내용".into());
    co.insert("당기중종속기업변동���용".into(), "연결대상변동내용".into());
    co.insert("당기연결대상회사의변동내용".into(), "연결대상변동내용".into());
    co.insert("본사의주소전화번호및홈페이지".into(), "본사의주소전화번호홈페이지".into());
    co.insert("본사의주소전화번호및홈페이지주소".into(), "���사의주소전화번호���페이지".into());
    co.insert("본사의주소전화번호홈페이지주소".into(), "본사의주소전화번호홈페이지".into());
    m.insert("companyOverview".into(), co);

    let mut bo = HashMap::new();
    bo.insert("생산및설비에관한사항".into(), "생산및설비".into());
    bo.insert("매출에관한사항".into(), "매출".into());
    bo.insert("주요원재료에관한사항".into(), "주요원재료".into());
    bo.insert("영업의개황등".into(), "영업현황".into());
    bo.insert("국내외시장여건등".into(), "시��여건".into());
    bo.insert("산업의특성등".into(), "산업의특성".into());
    bo.insert("사업부문별현황".into(), "사업부문현황".into());
    m.insert("businessOverview".into(), bo);

    let mut md = HashMap::new();
    md.insert("재무상태및영업실적연결기준".into(), "재무상태및영업실적".into());
    md.insert("조직개편".into(), "조직변경".into());
    md.insert("조직의변경".into(), "조직변경".into());
    md.insert("조직변경등".into(), "조직변경".into());
    md.insert("자산손상인식".into(), "자산손상".into());
    md.insert("유동성및자금조달과지출".into(), "유동성및자금조달".into());
    md.insert("환율변동영향".into(), "환율변동".into());
    m.insert("mdna".into(), md);

    let mut au = HashMap::new();
    au.insert("감사위원회에관한��항".into(), "감사위원회".into());
    au.insert("감사위원회의위원의독립성".into(), "감사위원회위원의독립성".into());
    au.insert("감사위원회의주요활동내역".into(), "감사위원회주요활동내역".into());
    au.insert("준법지원인등지원조직현��".into(), "준법지원인지원조직현황".into());
    m.insert("auditSystem".into(), au);

    m
});

fn body_anchor(text: &str) -> String {
    let normalized: String = text.split_whitespace().collect::<Vec<&str>>().join(" ");
    if normalized.is_empty() {
        return "empty".to_string();
    }
    let anchor: String = normalized.chars().take(96).collect();
    let mut hasher = Blake2b::<U8>::new();
    hasher.update(anchor.as_bytes());
    let result = hasher.finalize();
    hex::encode(&result[..6])
}

fn canonical_heading_key(
    label_text: &str,
    label_key: &str,
    level: i64,
    topic: Option<&str>,
    section_mappings: Option<&HashMap<String, String>>,
) -> String {
    if level <= 3 {
        if let Some(t) = topic {
            if !t.is_empty() {
                if let Some(mappings) = section_mappings {
                    if let Some(mapped) = mappings.get(label_text) {
                        if mapped == t {
                            return format!("@topic:{}", t);
                        }
                    }
                }
            }
        }
    }
    label_key.to_string()
}

struct PathInfo {
    path_text: Option<String>,
    path_key: Option<String>,
    parent_path_key: Option<String>,
    semantic_path_key: Option<String>,
    semantic_parent_path_key: Option<String>,
}

fn build_path_info(stack: &[StackEntry]) -> PathInfo {
    if stack.is_empty() {
        return PathInfo {
            path_text: None,
            path_key: None,
            parent_path_key: None,
            semantic_path_key: None,
            semantic_parent_path_key: None,
        };
    }

    let labels: Vec<&str> = stack.iter().map(|s| s.label.as_str()).collect();
    let keys: Vec<&str> = stack.iter().filter(|s| !s.key.is_empty()).map(|s| s.key.as_str()).collect();
    let sem_keys: Vec<&str> = stack.iter().filter(|s| !s.semantic_key.is_empty()).map(|s| s.semantic_key.as_str()).collect();

    PathInfo {
        path_text: if labels.is_empty() { None } else { Some(labels.join(" > ")) },
        path_key: if keys.is_empty() { None } else { Some(keys.join(" > ")) },
        parent_path_key: if keys.len() > 1 { Some(keys[..keys.len() - 1].join(" > ")) } else { None },
        semantic_path_key: if sem_keys.is_empty() { None } else { Some(sem_keys.join(" > ")) },
        semantic_parent_path_key: if sem_keys.len() > 1 { Some(sem_keys[..sem_keys.len() - 1].join(" > ")) } else { None },
    }
}

pub fn parse_text_structure_with_state(
    text: &str,
    _source_block_order: i64,
    topic: Option<&str>,
    initial_headings: &[StackEntry],
    section_mappings: Option<&HashMap<String, String>>,
) -> (Vec<TextNode>, Vec<StackEntry>) {
    let mut nodes: Vec<TextNode> = Vec::new();
    let mut stack: Vec<StackEntry> = initial_headings.to_vec();
    let mut body_lines: Vec<String> = Vec::new();
    let mut segment_order: i64 = 0;

    // Inline flush_body
    let mut flush_body = |nodes: &mut Vec<TextNode>,
                           stack: &[StackEntry],
                           body_lines: &mut Vec<String>,
                           segment_order: &mut i64| {
        let body: String = body_lines.join("\n").trim().to_string();
        body_lines.clear();
        if body.is_empty() {
            return;
        }

        let info = build_path_info(stack);
        let level = stack.last().map_or(0, |s| s.level);
        let anchor = body_anchor(&body);
        let stable_key_base = if let Some(ref spk) = info.semantic_path_key {
            format!("body|p:{}", spk)
        } else {
            format!("body|lv:{}|a:{}", level, anchor)
        };

        nodes.push(TextNode {
            text_node_type: "body".to_string(),
            text_structural: true,
            text_level: level,
            text_path: info.path_text,
            text_path_key: info.path_key,
            text_parent_path_key: info.parent_path_key,
            text_semantic_path_key: info.semantic_path_key,
            text_semantic_parent_path_key: info.semantic_parent_path_key,
            segment_order: *segment_order,
            segment_key_base: stable_key_base,
            text: body,
        });
        *segment_order += 1;
    };

    for raw_line in text.lines() {
        let line = heading::clean_line(raw_line);
        let stripped = line.trim();
        if stripped.is_empty() {
            if !body_lines.is_empty() {
                body_lines.push(String::new());
            }
            continue;
        }

        let heading_result = heading::detect_heading(stripped);
        if heading_result.is_none() {
            body_lines.push(stripped.to_string());
            continue;
        }

        flush_body(&mut nodes, &stack, &mut body_lines, &mut segment_order);
        let (level, label, structural) = heading_result.unwrap();
        let label_text = heading::normalize_heading_text(&label);
        let label_key = heading::heading_key(&label);
        let stack_key =
            canonical_heading_key(&label_text, &label_key, level, topic, section_mappings);
        let semantic_stack_key =
            heading::semantic_segment_key(&stack_key, topic, &TOPIC_SEGMENT_ALIASES);

        let redundant_topic_alias = structural
            && !stack.is_empty()
            && level <= 3
            && stack_key.starts_with("@topic:")
            && stack.last().unwrap().level == level
            && stack.last().unwrap().key == stack_key;

        let (path_text, path_key, parent_path_key, semantic_path_key, semantic_parent_path_key, segment_key_base);

        if structural && !redundant_topic_alias {
            while !stack.is_empty() && stack.last().unwrap().level >= level {
                stack.pop();
            }
            stack.push(StackEntry {
                level,
                label: label_text.clone(),
                key: stack_key.clone(),
                semantic_key: semantic_stack_key.clone(),
            });
            let info = build_path_info(&stack);
            path_text = info.path_text;
            path_key = info.path_key;
            parent_path_key = info.parent_path_key;
            semantic_path_key = info.semantic_path_key.clone();
            semantic_parent_path_key = info.semantic_parent_path_key;
            segment_key_base = format!(
                "heading|lv:{}|p:{}",
                level,
                semantic_path_key
                    .as_deref()
                    .unwrap_or(&semantic_stack_key)
            );
        } else {
            let current_keys: Vec<&str> = stack
                .iter()
                .filter(|s| !s.key.is_empty())
                .map(|s| s.key.as_str())
                .collect();
            let current_sem_keys: Vec<&str> = stack
                .iter()
                .filter(|s| !s.semantic_key.is_empty())
                .map(|s| s.semantic_key.as_str())
                .collect();
            path_text = Some(label_text.clone());
            let key_prefix = if redundant_topic_alias {
                "@alias"
            } else {
                "@marker"
            };
            path_key = Some(format!("{}:{}", key_prefix, label_key));
            parent_path_key = if current_keys.is_empty() {
                None
            } else {
                Some(current_keys.join(" > "))
            };
            let spk = format!("{}:{}", key_prefix, label_key);
            semantic_path_key = Some(spk.clone());
            semantic_parent_path_key = if current_sem_keys.is_empty() {
                None
            } else {
                Some(current_sem_keys.join(" > "))
            };
            let segment_kind = if redundant_topic_alias {
                "alias"
            } else {
                "marker"
            };
            segment_key_base = format!(
                "heading|{}|lv:{}|p:{}",
                segment_kind, level, spk
            );
        }

        nodes.push(TextNode {
            text_node_type: "heading".to_string(),
            text_structural: structural && !redundant_topic_alias,
            text_level: level,
            text_path: path_text,
            text_path_key: path_key,
            text_parent_path_key: parent_path_key,
            text_semantic_path_key: semantic_path_key,
            text_semantic_parent_path_key: semantic_parent_path_key,
            segment_order,
            segment_key_base,
            text: stripped.to_string(),
        });
        segment_order += 1;
    }

    flush_body(&mut nodes, &stack, &mut body_lines, &mut segment_order);
    (nodes, stack)
}
