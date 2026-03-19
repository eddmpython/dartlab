//! dartlab-core — sections 파이프라인 Rust 가속 코어
//!
//! Phase 1: 잎 함수 (순수 문자열 처리)
//! - content: _splitContentBlocks (318ms → ~10ms)
//! - heading: _detect_heading + _normalize + _heading_key
//! - mapper: normalizeSectionTitle + mapSectionTitle
//! - chunker: parseMajorNum

mod chunker;
mod content;
mod heading;
mod mapper;
mod pipeline;

use pyo3::prelude::*;

/// content를 text/table block으로 분해
#[pyfunction]
fn split_content_blocks(content: &str) -> Vec<(String, String)> {
    content::split_content_blocks(content)
}

/// heading 감지: (level, label, structural) 또는 None
#[pyfunction]
fn detect_heading(line: &str) -> Option<(u8, String, bool)> {
    heading::detect_heading(line)
}

/// heading 라벨 정규화
#[pyfunction]
fn normalize_heading_text(text: &str) -> String {
    heading::normalize_heading_text(text)
}

/// heading identity key
#[pyfunction]
fn heading_key(text: &str) -> String {
    heading::heading_key(text)
}

/// 시점 마커 여부
#[pyfunction]
fn is_temporal_marker(text: &str) -> bool {
    heading::is_temporal_marker(text)
}

/// 잎 번호 접두사 제거
#[pyfunction]
fn strip_section_prefix(title: &str) -> String {
    heading::strip_section_prefix(title)
}

/// section title 정규화
#[pyfunction]
fn normalize_section_title(title: &str) -> String {
    mapper::normalize_section_title(title)
}

/// title → topic 매핑
#[pyfunction]
fn map_section_title(title: &str) -> String {
    mapper::map_section_title(title)
}

/// 장 번호 추출 (로마숫자)
#[pyfunction]
fn parse_major_num(title: &str) -> Option<u8> {
    chunker::parse_major_num(title)
}

// ── pipeline API (Phase 2+3 합성) ──

/// 1기간 분량의 (titles, contents) → 확장된 행 칼럼 dict
#[pyfunction]
fn process_period(
    py: Python<'_>,
    titles: Vec<String>,
    contents: Vec<String>,
) -> PyResult<PyObject> {
    let result = pipeline::process_period(&titles, &contents);

    let dict = pyo3::types::PyDict::new(py);
    dict.set_item("chapter", result.chapters)?;
    dict.set_item("topic", result.topics)?;
    dict.set_item("blockType", result.block_types)?;
    dict.set_item("blockOrder", result.block_orders)?;
    dict.set_item("sourceBlockOrder", result.source_block_orders)?;
    dict.set_item("text", result.texts)?;
    dict.set_item("majorNum", result.major_nums)?;
    dict.set_item("orderSeq", result.order_seqs)?;
    dict.set_item("sourceTopic", result.source_topics)?;
    dict.set_item("textNodeType", result.text_node_types)?;
    dict.set_item("textStructural", result.text_structurals)?;
    dict.set_item("textLevel", result.text_levels)?;
    dict.set_item("textPath", result.text_paths)?;
    dict.set_item("textPathKey", result.text_path_keys)?;
    dict.set_item("textParentPathKey", result.text_parent_path_keys)?;
    dict.set_item("textSemanticPathKey", result.text_semantic_path_keys)?;
    dict.set_item("textSemanticParentPathKey", result.text_semantic_parent_path_keys)?;
    dict.set_item("segmentOrder", result.segment_orders)?;
    dict.set_item("segmentKey", result.segment_keys)?;
    dict.set_item("sortOrder", result.sort_orders)?;
    Ok(dict.into())
}

// ── 배치 API (FFI 오버헤드 제거) ──

/// content 리스트를 한 번에 분해 → 각 content별 블록 리스트
#[pyfunction]
fn split_content_blocks_batch(contents: Vec<String>) -> Vec<Vec<(String, String)>> {
    contents
        .iter()
        .map(|c| content::split_content_blocks(c))
        .collect()
}

/// title 리스트를 한 번에 매핑 → topic 리스트
#[pyfunction]
fn map_section_titles_batch(titles: Vec<String>) -> Vec<String> {
    titles
        .iter()
        .map(|t| mapper::map_section_title(t))
        .collect()
}

/// heading 감지 배치
#[pyfunction]
fn detect_headings_batch(lines: Vec<String>) -> Vec<Option<(u8, String, bool)>> {
    lines
        .iter()
        .map(|l| heading::detect_heading(l))
        .collect()
}

/// Python 모듈 등록
#[pymodule]
fn dartlab_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(split_content_blocks, m)?)?;
    m.add_function(wrap_pyfunction!(detect_heading, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_heading_text, m)?)?;
    m.add_function(wrap_pyfunction!(heading_key, m)?)?;
    m.add_function(wrap_pyfunction!(is_temporal_marker, m)?)?;
    m.add_function(wrap_pyfunction!(strip_section_prefix, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_section_title, m)?)?;
    m.add_function(wrap_pyfunction!(map_section_title, m)?)?;
    m.add_function(wrap_pyfunction!(parse_major_num, m)?)?;
    // batch API
    m.add_function(wrap_pyfunction!(split_content_blocks_batch, m)?)?;
    m.add_function(wrap_pyfunction!(map_section_titles_batch, m)?)?;
    m.add_function(wrap_pyfunction!(detect_headings_batch, m)?)?;
    // pipeline API
    m.add_function(wrap_pyfunction!(process_period, m)?)?;
    Ok(())
}
