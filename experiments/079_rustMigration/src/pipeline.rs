//! 기간 단위 파이프라인 — _reportRowsToTopicRows + _expandStructuredRows 합성
//!
//! Python 루프를 제거하고 Rust에서 한 번에 처리.
//! 입력: (title, content) 쌍 리스트
//! 출력: 확장된 행의 칼럼 벡터 (FFI 최적)

use crate::chunker::parse_major_num;
use crate::content::split_content_blocks;
use crate::heading::{
    detect_heading, heading_key, is_temporal_marker, normalize_heading_text, strip_section_prefix,
};
use crate::mapper::map_section_title;

use blake2::{Blake2b, Digest};
use blake2::digest::consts::U8;

// ── semantic segment aliases (textStructure.py) ──

use once_cell::sync::Lazy;
use regex::Regex;
use std::collections::HashMap;

static TOPIC_SEGMENT_ALIASES: Lazy<HashMap<&str, HashMap<&str, &str>>> = Lazy::new(|| {
    let mut m: HashMap<&str, HashMap<&str, &str>> = HashMap::new();
    let mut co: HashMap<&str, &str> = HashMap::new();
    co.insert("연결대상종속기업개황", "연결대상종속사현황");
    co.insert("연결대상종속회사개황", "연결대상종속사현황");
    co.insert("연결대상종속기업현황", "연결대상종속사현황");
    co.insert("연결대상종속회사현황", "연결대상종속사현황");
    co.insert("연결대상종속회사현황요약", "연결대상종속사현황");
    co.insert("연결대상종속회사개황요약", "연결대상종속사현황");
    co.insert("연결대상종속기업개황요약", "연결대상종속사현황");
    co.insert("연결대상종속기업현황요약", "연결대상종속사현황");
    co.insert("연결대상회사의변동내용", "연결대상변동내용");
    co.insert("연결대상회사의변동현황", "연결대상변동내용");
    co.insert("당기중종속기업변동내용", "연결대상변동내용");
    co.insert("당기연결대상회사의변동내용", "연결대상변동내용");
    co.insert("본사의주소전화번호및홈페이지", "본사의주소전화번호홈페이지");
    co.insert("본사의주소전화번호및홈페이지주소", "본사의주소전화번호홈페이지");
    co.insert("본사의주소전화번호홈페이지주소", "본사의주소전화번호홈페이지");
    m.insert("companyOverview", co);

    let mut bo: HashMap<&str, &str> = HashMap::new();
    bo.insert("생산및설비에관한사항", "생산및설비");
    bo.insert("매출에관한사항", "매출");
    bo.insert("주요원재료에관한사항", "주요원재료");
    bo.insert("영업의개황등", "영업현황");
    bo.insert("국내외시장여건등", "시장여건");
    bo.insert("산업의특성등", "산업의특성");
    bo.insert("사업부문별현황", "사업부문현황");
    m.insert("businessOverview", bo);

    let mut md: HashMap<&str, &str> = HashMap::new();
    md.insert("재무상태및영업실적연결기준", "재무상태및영업실적");
    md.insert("조직개편", "조직변경");
    md.insert("조직의변경", "조직변경");
    md.insert("조직변경등", "조직변경");
    md.insert("자산손상인식", "자산손상");
    md.insert("유동성및자금조달과지출", "유동성및자금조달");
    md.insert("환율변동영향", "환율변동");
    m.insert("mdna", md);

    let mut au: HashMap<&str, &str> = HashMap::new();
    au.insert("감사위원회에관한사항", "감사위원회");
    au.insert("감사위원회의위원의독립성", "감사위원회위원의독립성");
    au.insert("감사위원회의주요활동내역", "감사위원회주요활동내역");
    au.insert("준법지원인등지원조직현황", "준법지원인지원조직현황");
    m.insert("auditSystem", au);
    m
});

static RE_SUFFIX_EGWANHAN: Lazy<Regex> = Lazy::new(|| Regex::new(r"에관한사항$").unwrap());

fn semantic_segment_key(label_key: &str, topic: &str) -> String {
    if label_key.is_empty() || label_key.starts_with('@') {
        return label_key.to_owned();
    }
    let mut key = label_key.to_owned();

    if let Some(alias_map) = TOPIC_SEGMENT_ALIASES.get(topic) {
        if let Some(&alias) = alias_map.get(key.as_str()) {
            key = alias.to_owned();
        }
    }
    key = RE_SUFFIX_EGWANHAN.replace(&key, "").to_string();
    key = key.replace("종속기업", "종속사").replace("종속회사", "종속사");
    if topic == "businessOverview" {
        key = key.replace("영업의개황", "영업현황");
    }
    if topic == "mdna" {
        key = key.replace("환율변동영향", "환율변동");
    }
    key
}

// ── chapter mapping ──

fn chapter_from_major_num(num: u8) -> Option<&'static str> {
    match num {
        1 => Some("I"),
        2 => Some("II"),
        3 => Some("III"),
        4 => Some("IV"),
        5 => Some("V"),
        6 => Some("VI"),
        7 => Some("VII"),
        8 => Some("VIII"),
        9 => Some("IX"),
        10 => Some("X"),
        11 => Some("XI"),
        12 => Some("XII"),
        _ => None,
    }
}

// ── body anchor (blake2b 8-byte hash) ──

fn body_anchor(text: &str) -> String {
    let normalized: String = text.split_whitespace().collect::<Vec<&str>>().join(" ");
    if normalized.is_empty() {
        return "empty".to_owned();
    }
    let anchor = if normalized.len() > 96 {
        &normalized[..normalized.char_indices().nth(96).map_or(normalized.len(), |(i, _)| i)]
    } else {
        &normalized
    };
    let mut hasher = Blake2b::<U8>::new();
    hasher.update(anchor.as_bytes());
    let result = hasher.finalize();
    hex::encode(&result[..6])
}

// hex encoding (no dependency)
mod hex {
    pub fn encode(bytes: &[u8]) -> String {
        bytes.iter().map(|b| format!("{:02x}", b)).collect()
    }
}

// ── heading state machine ──

#[derive(Clone)]
struct HeadingState {
    level: u8,
    label: String,
    key: String,
    semantic_key: String,
}

struct TextNode {
    node_type: &'static str, // "heading" | "body"
    structural: bool,
    level: u8,
    path: Option<String>,
    path_key: Option<String>,
    parent_path_key: Option<String>,
    semantic_path_key: Option<String>,
    semantic_parent_path_key: Option<String>,
    segment_order: u32,
    segment_key_base: String,
    text: String,
}

fn parse_text_structure(
    text: &str,
    topic: &str,
    initial_stack: &[HeadingState],
) -> (Vec<TextNode>, Vec<HeadingState>) {
    let mut nodes: Vec<TextNode> = Vec::new();
    let mut stack: Vec<HeadingState> = initial_stack.to_vec();
    let mut body_lines: Vec<String> = Vec::new();
    let mut segment_order: u32 = 0;

    let flush_body = |body_lines: &mut Vec<String>,
                      stack: &[HeadingState],
                      nodes: &mut Vec<TextNode>,
                      segment_order: &mut u32| {
        let body = body_lines.join("\n");
        let trimmed = body.trim();
        body_lines.clear();
        if trimmed.is_empty() {
            return;
        }

        let (path_labels, path_keys, semantic_keys) = extract_path_info(stack);
        let level = stack.last().map_or(0, |s| s.level);
        let anchor = body_anchor(trimmed);
        let semantic_pk = if !semantic_keys.is_empty() {
            Some(semantic_keys.join(" > "))
        } else {
            None
        };
        let seg_base = if let Some(ref spk) = semantic_pk {
            format!("body|p:{}", spk)
        } else {
            format!("body|lv:{}|a:{}", level, anchor)
        };

        nodes.push(TextNode {
            node_type: "body",
            structural: true,
            level,
            path: if path_labels.is_empty() {
                None
            } else {
                Some(path_labels.join(" > "))
            },
            path_key: if path_keys.is_empty() {
                None
            } else {
                Some(path_keys.join(" > "))
            },
            parent_path_key: if path_keys.len() > 1 {
                Some(path_keys[..path_keys.len() - 1].join(" > "))
            } else {
                None
            },
            semantic_path_key: semantic_pk,
            semantic_parent_path_key: if semantic_keys.len() > 1 {
                Some(semantic_keys[..semantic_keys.len() - 1].join(" > "))
            } else {
                None
            },
            segment_order: *segment_order,
            segment_key_base: seg_base,
            text: trimmed.to_owned(),
        });
        *segment_order += 1;
    };

    for raw_line in text.lines() {
        let line = raw_line.replace('\u{00a0}', " ").replace('\t', " ");
        let stripped = line.trim();
        if stripped.is_empty() {
            if !body_lines.is_empty() {
                body_lines.push(String::new());
            }
            continue;
        }

        let heading = detect_heading(stripped);
        if heading.is_none() {
            body_lines.push(stripped.to_owned());
            continue;
        }

        flush_body(&mut body_lines, &stack, &mut nodes, &mut segment_order);
        let (level, label, structural) = heading.unwrap();
        let label_text = normalize_heading_text(&label);
        let label_key = heading_key(&label);

        // canonical key
        let stack_key = if level == 1 {
            let mapped = map_section_title(&label_text);
            if mapped == topic {
                format!("@topic:{}", topic)
            } else {
                label_key.clone()
            }
        } else {
            label_key.clone()
        };
        let semantic_stack_key = semantic_segment_key(&stack_key, topic);

        // redundant topic alias check
        let redundant = structural
            && !stack.is_empty()
            && level == 1
            && stack_key.starts_with("@topic:")
            && stack.last().unwrap().level == level
            && stack.last().unwrap().key == stack_key;

        if structural && !redundant {
            while stack.last().map_or(false, |s| s.level >= level) {
                stack.pop();
            }
            stack.push(HeadingState {
                level,
                label: label_text.clone(),
                key: stack_key.clone(),
                semantic_key: semantic_stack_key.clone(),
            });
            let (path_labels, path_keys, semantic_keys) = extract_path_info(&stack);
            let pk = if path_keys.is_empty() { None } else { Some(path_keys.join(" > ")) };
            let ppk = if path_keys.len() > 1 { Some(path_keys[..path_keys.len()-1].join(" > ")) } else { None };
            let spk = if semantic_keys.is_empty() { None } else { Some(semantic_keys.join(" > ")) };
            let sppk = if semantic_keys.len() > 1 { Some(semantic_keys[..semantic_keys.len()-1].join(" > ")) } else { None };
            let seg_base = format!("heading|lv:{}|p:{}", level, spk.as_deref().unwrap_or(&semantic_stack_key));

            nodes.push(TextNode {
                node_type: "heading",
                structural: true,
                level,
                path: if path_labels.is_empty() { None } else { Some(path_labels.join(" > ")) },
                path_key: pk,
                parent_path_key: ppk,
                semantic_path_key: spk,
                semantic_parent_path_key: sppk,
                segment_order,
                segment_key_base: seg_base,
                text: stripped.to_owned(),
            });
        } else {
            let current_keys: Vec<String> = stack.iter().filter(|s| !s.key.is_empty()).map(|s| s.key.clone()).collect();
            let current_semantic: Vec<String> = stack.iter().filter(|s| !s.semantic_key.is_empty()).map(|s| s.semantic_key.clone()).collect();
            let key_prefix = if redundant { "@alias" } else { "@marker" };
            let path_key = format!("{}:{}", key_prefix, label_key);
            let seg_kind = if redundant { "alias" } else { "marker" };
            let seg_base = format!("heading|{}|lv:{}|p:{}", seg_kind, level, path_key);

            nodes.push(TextNode {
                node_type: "heading",
                structural: false,
                level,
                path: Some(label_text.clone()),
                path_key: Some(path_key.clone()),
                parent_path_key: if current_keys.is_empty() { None } else { Some(current_keys.join(" > ")) },
                semantic_path_key: Some(path_key),
                semantic_parent_path_key: if current_semantic.is_empty() { None } else { Some(current_semantic.join(" > ")) },
                segment_order,
                segment_key_base: seg_base,
                text: stripped.to_owned(),
            });
        }
        segment_order += 1;
    }

    flush_body(&mut body_lines, &stack, &mut nodes, &mut segment_order);
    (nodes, stack)
}

fn extract_path_info(stack: &[HeadingState]) -> (Vec<String>, Vec<String>, Vec<String>) {
    let labels: Vec<String> = stack.iter().map(|s| s.label.clone()).collect();
    let keys: Vec<String> = stack.iter().filter(|s| !s.key.is_empty()).map(|s| s.key.clone()).collect();
    let semantic: Vec<String> = stack.iter().filter(|s| !s.semantic_key.is_empty()).map(|s| s.semantic_key.clone()).collect();
    (labels, keys, semantic)
}

// ── 결과 구조 (칼럼 지향) ──

/// process_period의 반환값 — 칼럼 벡터
pub struct PeriodResult {
    pub chapters: Vec<String>,
    pub topics: Vec<String>,
    pub block_types: Vec<String>,
    pub block_orders: Vec<u32>,
    pub source_block_orders: Vec<u32>,
    pub texts: Vec<String>,
    pub major_nums: Vec<u8>,
    pub order_seqs: Vec<u32>,
    pub source_topics: Vec<String>,
    // text structure metadata
    pub text_node_types: Vec<Option<String>>,
    pub text_structurals: Vec<Option<bool>>,
    pub text_levels: Vec<Option<u8>>,
    pub text_paths: Vec<Option<String>>,
    pub text_path_keys: Vec<Option<String>>,
    pub text_parent_path_keys: Vec<Option<String>>,
    pub text_semantic_path_keys: Vec<Option<String>>,
    pub text_semantic_parent_path_keys: Vec<Option<String>>,
    pub segment_orders: Vec<u32>,
    pub segment_keys: Vec<String>,
    pub sort_orders: Vec<u32>,
}

/// 1기간 분량의 (title, content) 쌍을 처리하여 확장된 행 칼럼 벡터를 반환
pub fn process_period(titles: &[String], contents: &[String]) -> PeriodResult {
    // Phase 1: _reportRowsToTopicRows
    struct RawRow {
        chapter: String,
        topic: String,
        block_type: String,
        block_order: u32,
        source_block_order: u32,
        text: String,
        major_num: u8,
        order_seq: u32,
        source_topic: String,
    }

    let mut raw_rows: Vec<RawRow> = Vec::new();
    let mut current_major: Option<u8> = None;
    let mut pending: Option<(String, String)> = None; // (title, content)
    let mut topic_block_counts: HashMap<(String, String), u32> = HashMap::new();
    let mut idx: u32 = 0;

    let mut register_content = |ch: &str,
                                tp: &str,
                                raw_title: &str,
                                content: &str,
                                major: u8,
                                idx: &mut u32,
                                counts: &mut HashMap<(String, String), u32>,
                                rows: &mut Vec<RawRow>| {
        let key = (ch.to_owned(), tp.to_owned());
        let mut next_order = *counts.get(&key).unwrap_or(&0);
        for (bt, bt_text) in split_content_blocks(content) {
            rows.push(RawRow {
                chapter: ch.to_owned(),
                topic: tp.to_owned(),
                block_type: bt,
                block_order: next_order,
                source_block_order: next_order,
                text: bt_text,
                major_num: major,
                order_seq: *idx,
                source_topic: raw_title.to_owned(),
            });
            next_order += 1;
            *idx += 1;
        }
        counts.insert(key, next_order);
    };

    for i in 0..titles.len() {
        let title = titles[i].trim();
        let content = contents[i].trim();
        if title.is_empty() || content.is_empty() {
            continue;
        }

        if let Some(major_num) = parse_major_num(title) {
            // flush pending
            if let Some((pt, pc)) = pending.take() {
                if let Some(pm) = parse_major_num(&pt) {
                    if let Some(ch) = chapter_from_major_num(pm) {
                        let raw_t = strip_section_prefix(&pt);
                        let tp = map_section_title(&raw_t);
                        register_content(ch, &tp, &raw_t, &pc, pm, &mut idx, &mut topic_block_counts, &mut raw_rows);
                    }
                }
            }
            current_major = Some(major_num);
            pending = Some((title.to_owned(), content.to_owned()));
            continue;
        }

        if current_major.is_none() {
            continue;
        }

        // flush pending chapter
        if let Some((pt, pc)) = pending.take() {
            if let Some(pm) = parse_major_num(&pt) {
                if let Some(ch) = chapter_from_major_num(pm) {
                    let raw_t = strip_section_prefix(&pt);
                    let tp = map_section_title(&raw_t);
                    register_content(ch, &tp, &raw_t, &pc, pm, &mut idx, &mut topic_block_counts, &mut raw_rows);
                }
            }
        }

        let major = current_major.unwrap();
        if let Some(ch) = chapter_from_major_num(major) {
            let raw_title = strip_section_prefix(title);
            let tp = map_section_title(&raw_title);
            register_content(ch, &tp, &raw_title, content, major, &mut idx, &mut topic_block_counts, &mut raw_rows);
        }
    }

    // flush final pending
    if let Some((pt, pc)) = pending.take() {
        if let Some(pm) = parse_major_num(&pt) {
            if let Some(ch) = chapter_from_major_num(pm) {
                let raw_t = strip_section_prefix(&pt);
                let tp = map_section_title(&raw_t);
                register_content(ch, &tp, &raw_t, &pc, pm, &mut idx, &mut topic_block_counts, &mut raw_rows);
            }
        }
    }

    // Phase 2: _expandStructuredRows (text structure + occurrence counting)
    let capacity = raw_rows.len() * 2;
    let mut result = PeriodResult {
        chapters: Vec::with_capacity(capacity),
        topics: Vec::with_capacity(capacity),
        block_types: Vec::with_capacity(capacity),
        block_orders: Vec::with_capacity(capacity),
        source_block_orders: Vec::with_capacity(capacity),
        texts: Vec::with_capacity(capacity),
        major_nums: Vec::with_capacity(capacity),
        order_seqs: Vec::with_capacity(capacity),
        source_topics: Vec::with_capacity(capacity),
        text_node_types: Vec::with_capacity(capacity),
        text_structurals: Vec::with_capacity(capacity),
        text_levels: Vec::with_capacity(capacity),
        text_paths: Vec::with_capacity(capacity),
        text_path_keys: Vec::with_capacity(capacity),
        text_parent_path_keys: Vec::with_capacity(capacity),
        text_semantic_path_keys: Vec::with_capacity(capacity),
        text_semantic_parent_path_keys: Vec::with_capacity(capacity),
        segment_orders: Vec::with_capacity(capacity),
        segment_keys: Vec::with_capacity(capacity),
        sort_orders: Vec::with_capacity(capacity),
    };

    let mut heading_state_by_topic: HashMap<String, Vec<HeadingState>> = HashMap::new();
    // (topic, seg_base) → occurrence count
    let mut occurrence_map: HashMap<(String, String), u32> = HashMap::new();

    // Collect rows with temporary segment_key_base, then assign occurrence
    struct TempRow {
        chapter: String,
        topic: String,
        block_type: String,
        block_order: u32,
        source_block_order: u32,
        text: String,
        major_num: u8,
        order_seq: u32,
        source_topic: String,
        text_node_type: Option<String>,
        text_structural: Option<bool>,
        text_level: Option<u8>,
        text_path: Option<String>,
        text_path_key: Option<String>,
        text_parent_path_key: Option<String>,
        text_semantic_path_key: Option<String>,
        text_semantic_parent_path_key: Option<String>,
        segment_order: u32,
        segment_key_base: String,
        sort_order: u32,
    }

    let mut temp_rows: Vec<TempRow> = Vec::with_capacity(capacity);

    for raw in &raw_rows {
        if raw.block_type != "text" {
            temp_rows.push(TempRow {
                chapter: raw.chapter.clone(),
                topic: raw.topic.clone(),
                block_type: raw.block_type.clone(),
                block_order: raw.block_order,
                source_block_order: raw.source_block_order,
                text: raw.text.clone(),
                major_num: raw.major_num,
                order_seq: raw.order_seq,
                source_topic: raw.source_topic.clone(),
                text_node_type: None,
                text_structural: None,
                text_level: None,
                text_path: None,
                text_path_key: None,
                text_parent_path_key: None,
                text_semantic_path_key: None,
                text_semantic_parent_path_key: None,
                segment_order: 0,
                segment_key_base: format!("table|sb:{}", raw.source_block_order),
                sort_order: raw.order_seq * 1000,
            });
            continue;
        }

        let initial = heading_state_by_topic
            .get(&raw.topic)
            .cloned()
            .unwrap_or_default();

        let (nodes, final_stack) = parse_text_structure(&raw.text, &raw.topic, &initial);
        heading_state_by_topic.insert(raw.topic.clone(), final_stack.clone());

        if nodes.is_empty() {
            // fallback: single body node
            let (_, path_keys, semantic_keys) = extract_path_info(&final_stack);
            let level = final_stack.last().map_or(0, |s| s.level);
            let spk = if semantic_keys.is_empty() { None } else { Some(semantic_keys.join(" > ")) };
            let seg_base = if let Some(ref sk) = spk {
                format!("body|p:{}", sk)
            } else {
                format!("body|lv:0|a:empty")
            };

            temp_rows.push(TempRow {
                chapter: raw.chapter.clone(),
                topic: raw.topic.clone(),
                block_type: "text".to_owned(),
                block_order: raw.block_order,
                source_block_order: raw.source_block_order,
                text: raw.text.clone(),
                major_num: raw.major_num,
                order_seq: raw.order_seq,
                source_topic: raw.source_topic.clone(),
                text_node_type: Some("body".to_owned()),
                text_structural: Some(true),
                text_level: Some(level),
                text_path: if path_keys.is_empty() { None } else { Some(path_keys.join(" > ")) },
                text_path_key: if path_keys.is_empty() { None } else { Some(path_keys.join(" > ")) },
                text_parent_path_key: if path_keys.len() > 1 { Some(path_keys[..path_keys.len()-1].join(" > ")) } else { None },
                text_semantic_path_key: spk.clone(),
                text_semantic_parent_path_key: if semantic_keys.len() > 1 { Some(semantic_keys[..semantic_keys.len()-1].join(" > ")) } else { None },
                segment_order: 0,
                segment_key_base: seg_base,
                sort_order: raw.order_seq * 1000,
            });
            continue;
        }

        for node in &nodes {
            temp_rows.push(TempRow {
                chapter: raw.chapter.clone(),
                topic: raw.topic.clone(),
                block_type: "text".to_owned(),
                block_order: raw.block_order,
                source_block_order: raw.source_block_order,
                text: node.text.clone(),
                major_num: raw.major_num,
                order_seq: raw.order_seq,
                source_topic: raw.source_topic.clone(),
                text_node_type: Some(node.node_type.to_owned()),
                text_structural: Some(node.structural),
                text_level: Some(node.level),
                text_path: node.path.clone(),
                text_path_key: node.path_key.clone(),
                text_parent_path_key: node.parent_path_key.clone(),
                text_semantic_path_key: node.semantic_path_key.clone(),
                text_semantic_parent_path_key: node.semantic_parent_path_key.clone(),
                segment_order: node.segment_order,
                segment_key_base: node.segment_key_base.clone(),
                sort_order: raw.order_seq * 1000 + node.segment_order,
            });
        }
    }

    // Sort by (topic, sort_order) for occurrence counting
    temp_rows.sort_by(|a, b| {
        a.topic.cmp(&b.topic).then(a.sort_order.cmp(&b.sort_order))
    });

    // Occurrence counting
    for row in &temp_rows {
        let occ_key = (row.topic.clone(), row.segment_key_base.clone());
        let count = occurrence_map.entry(occ_key).or_insert(0);
        *count += 1;
        let occ = *count;
        let seg_key = format!("{}|occ:{}", row.segment_key_base, occ);

        result.chapters.push(row.chapter.clone());
        result.topics.push(row.topic.clone());
        result.block_types.push(row.block_type.clone());
        result.block_orders.push(row.block_order);
        result.source_block_orders.push(row.source_block_order);
        result.texts.push(row.text.clone());
        result.major_nums.push(row.major_num);
        result.order_seqs.push(row.order_seq);
        result.source_topics.push(row.source_topic.clone());
        result.text_node_types.push(row.text_node_type.clone());
        result.text_structurals.push(row.text_structural);
        result.text_levels.push(row.text_level);
        result.text_paths.push(row.text_path.clone());
        result.text_path_keys.push(row.text_path_key.clone());
        result.text_parent_path_keys.push(row.text_parent_path_key.clone());
        result.text_semantic_path_keys.push(row.text_semantic_path_key.clone());
        result.text_semantic_parent_path_keys.push(row.text_semantic_parent_path_key.clone());
        result.segment_orders.push(row.segment_order);
        result.segment_keys.push(seg_key);
        result.sort_orders.push(row.sort_order);
    }

    result
}
