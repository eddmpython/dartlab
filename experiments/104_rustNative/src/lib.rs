use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

mod heading;
mod text_structure;

use text_structure::parse_text_structure_with_state;

/// Rust implementation of parseTextStructureWithState.
/// Returns (nodes: list[dict], finalStack: list[dict]).
#[pyfunction]
#[pyo3(signature = (text, *, source_block_order, topic=None, initial_headings=None, section_mappings=None))]
fn parse_text_structure(
    py: Python<'_>,
    text: &str,
    source_block_order: i64,
    topic: Option<&str>,
    initial_headings: Option<&Bound<'_, PyList>>,
    section_mappings: Option<&Bound<'_, PyDict>>,
) -> PyResult<PyObject> {
    let init_stack = match initial_headings {
        Some(list) => {
            let mut v = Vec::new();
            for item in list.iter() {
                let d = item.downcast::<PyDict>()?;
                let level: i64 = d.get_item("level")?.unwrap().extract()?;
                let label: String = d.get_item("label")?.unwrap().extract()?;
                let key: String = d.get_item("key")?.unwrap().extract()?;
                let semantic_key: String = d.get_item("semanticKey")?.unwrap().extract()?;
                v.push(text_structure::StackEntry {
                    level,
                    label,
                    key,
                    semantic_key,
                });
            }
            v
        }
        None => Vec::new(),
    };

    let mappings: Option<std::collections::HashMap<String, String>> = match section_mappings {
        Some(dict) => {
            let mut m = std::collections::HashMap::new();
            for (k, v) in dict.iter() {
                let ks: String = k.extract()?;
                let vs: String = v.extract()?;
                m.insert(ks, vs);
            }
            Some(m)
        }
        None => None,
    };

    let (nodes, final_stack) =
        parse_text_structure_with_state(text, source_block_order, topic, &init_stack, mappings.as_ref());

    // Convert to Python objects
    let py_nodes = PyList::empty(py);
    for node in &nodes {
        let d = PyDict::new(py);
        d.set_item("textNodeType", &node.text_node_type)?;
        d.set_item("textStructural", node.text_structural)?;
        d.set_item("textLevel", node.text_level)?;
        d.set_item("textPath", node.text_path.as_deref())?;
        d.set_item("textPathKey", node.text_path_key.as_deref())?;
        d.set_item("textParentPathKey", node.text_parent_path_key.as_deref())?;
        d.set_item("textSemanticPathKey", node.text_semantic_path_key.as_deref())?;
        d.set_item("textSemanticParentPathKey", node.text_semantic_parent_path_key.as_deref())?;
        d.set_item("segmentOrder", node.segment_order)?;
        d.set_item("segmentKeyBase", &node.segment_key_base)?;
        d.set_item("text", &node.text)?;
        py_nodes.append(d)?;
    }

    let py_stack = PyList::empty(py);
    for entry in &final_stack {
        let d = PyDict::new(py);
        d.set_item("level", entry.level)?;
        d.set_item("label", &entry.label)?;
        d.set_item("key", &entry.key)?;
        d.set_item("semanticKey", &entry.semantic_key)?;
        py_stack.append(d)?;
    }

    let result = PyList::empty(py);
    result.append(py_nodes)?;
    result.append(py_stack)?;
    Ok(result.into_any().unbind())
}

/// Batch version: process all text blocks at once, minimizing Python/Rust boundary crossings.
/// texts: list of (text, topic, source_block_order) tuples
/// Returns list of (nodes, finalStack) tuples.
#[pyfunction]
#[pyo3(signature = (blocks, section_mappings=None))]
fn parse_text_structure_batch(
    py: Python<'_>,
    blocks: Vec<(String, Option<String>, i64)>,
    section_mappings: Option<&Bound<'_, PyDict>>,
) -> PyResult<PyObject> {
    let mappings: Option<std::collections::HashMap<String, String>> = match section_mappings {
        Some(dict) => {
            let mut m = std::collections::HashMap::new();
            for (k, v) in dict.iter() {
                let ks: String = k.extract()?;
                let vs: String = v.extract()?;
                m.insert(ks, vs);
            }
            Some(m)
        }
        None => None,
    };

    // Process all blocks in Rust -- no Python/Rust boundary per block
    let mut all_results: Vec<(Vec<text_structure::TextNode>, Vec<text_structure::StackEntry>)> =
        Vec::with_capacity(blocks.len());

    // Maintain heading state per topic across blocks (like Python pipeline does)
    let mut heading_state: std::collections::HashMap<String, Vec<text_structure::StackEntry>> =
        std::collections::HashMap::new();

    for (text, topic, sbo) in &blocks {
        let topic_str = topic.as_deref();
        let topic_key = topic.clone().unwrap_or_default();
        let init = heading_state.get(&topic_key).cloned().unwrap_or_default();
        let (nodes, final_stack) =
            parse_text_structure_with_state(text, *sbo, topic_str, &init, mappings.as_ref());
        heading_state.insert(topic_key, final_stack.clone());
        all_results.push((nodes, final_stack));
    }

    // Convert to Python only once at the end
    let py_results = PyList::empty(py);
    for (nodes, final_stack) in &all_results {
        let py_nodes = PyList::empty(py);
        for node in nodes {
            let d = PyDict::new(py);
            d.set_item("textNodeType", &node.text_node_type)?;
            d.set_item("textStructural", node.text_structural)?;
            d.set_item("textLevel", node.text_level)?;
            d.set_item("textPath", node.text_path.as_deref())?;
            d.set_item("textPathKey", node.text_path_key.as_deref())?;
            d.set_item("textParentPathKey", node.text_parent_path_key.as_deref())?;
            d.set_item("textSemanticPathKey", node.text_semantic_path_key.as_deref())?;
            d.set_item("textSemanticParentPathKey", node.text_semantic_parent_path_key.as_deref())?;
            d.set_item("segmentOrder", node.segment_order)?;
            d.set_item("segmentKeyBase", &node.segment_key_base)?;
            d.set_item("text", &node.text)?;
            py_nodes.append(d)?;
        }

        let py_stack = PyList::empty(py);
        for entry in final_stack {
            let d = PyDict::new(py);
            d.set_item("level", entry.level)?;
            d.set_item("label", &entry.label)?;
            d.set_item("key", &entry.key)?;
            d.set_item("semanticKey", &entry.semantic_key)?;
            py_stack.append(d)?;
        }

        let pair = PyList::empty(py);
        pair.append(py_nodes)?;
        pair.append(py_stack)?;
        py_results.append(pair)?;
    }

    Ok(py_results.into_any().unbind())
}

/// Columnar batch: returns dict of lists (one list per field) for direct DataFrame construction.
/// This avoids creating thousands of Python dicts.
#[pyfunction]
#[pyo3(signature = (blocks, section_mappings=None))]
fn parse_text_structure_columnar(
    py: Python<'_>,
    blocks: Vec<(String, Option<String>, i64)>,
    section_mappings: Option<&Bound<'_, PyDict>>,
) -> PyResult<PyObject> {
    let mappings: Option<std::collections::HashMap<String, String>> = match section_mappings {
        Some(dict) => {
            let mut m = std::collections::HashMap::new();
            for (k, v) in dict.iter() {
                let ks: String = k.extract()?;
                let vs: String = v.extract()?;
                m.insert(ks, vs);
            }
            Some(m)
        }
        None => None,
    };

    // Estimate capacity
    let est_cap = blocks.len() * 30;

    let mut col_node_type: Vec<String> = Vec::with_capacity(est_cap);
    let mut col_structural: Vec<bool> = Vec::with_capacity(est_cap);
    let mut col_level: Vec<i64> = Vec::with_capacity(est_cap);
    let mut col_path: Vec<Option<String>> = Vec::with_capacity(est_cap);
    let mut col_path_key: Vec<Option<String>> = Vec::with_capacity(est_cap);
    let mut col_parent_path_key: Vec<Option<String>> = Vec::with_capacity(est_cap);
    let mut col_semantic_path_key: Vec<Option<String>> = Vec::with_capacity(est_cap);
    let mut col_semantic_parent_path_key: Vec<Option<String>> = Vec::with_capacity(est_cap);
    let mut col_segment_order: Vec<i64> = Vec::with_capacity(est_cap);
    let mut col_segment_key_base: Vec<String> = Vec::with_capacity(est_cap);
    let mut col_text: Vec<String> = Vec::with_capacity(est_cap);
    let mut col_block_idx: Vec<i64> = Vec::with_capacity(est_cap);

    let mut heading_state: std::collections::HashMap<String, Vec<text_structure::StackEntry>> =
        std::collections::HashMap::new();

    for (block_idx, (text, topic, sbo)) in blocks.iter().enumerate() {
        let topic_str = topic.as_deref();
        let topic_key = topic.clone().unwrap_or_default();
        let init = heading_state.get(&topic_key).cloned().unwrap_or_default();
        let (nodes, final_stack) =
            parse_text_structure_with_state(text, *sbo, topic_str, &init, mappings.as_ref());
        heading_state.insert(topic_key, final_stack);

        for node in nodes {
            col_node_type.push(node.text_node_type);
            col_structural.push(node.text_structural);
            col_level.push(node.text_level);
            col_path.push(node.text_path);
            col_path_key.push(node.text_path_key);
            col_parent_path_key.push(node.text_parent_path_key);
            col_semantic_path_key.push(node.text_semantic_path_key);
            col_semantic_parent_path_key.push(node.text_semantic_parent_path_key);
            col_segment_order.push(node.segment_order);
            col_segment_key_base.push(node.segment_key_base);
            col_text.push(node.text);
            col_block_idx.push(block_idx as i64);
        }
    }

    let result = PyDict::new(py);
    result.set_item("textNodeType", col_node_type)?;
    result.set_item("textStructural", col_structural)?;
    result.set_item("textLevel", col_level)?;
    result.set_item("textPath", col_path)?;
    result.set_item("textPathKey", col_path_key)?;
    result.set_item("textParentPathKey", col_parent_path_key)?;
    result.set_item("textSemanticPathKey", col_semantic_path_key)?;
    result.set_item("textSemanticParentPathKey", col_semantic_parent_path_key)?;
    result.set_item("segmentOrder", col_segment_order)?;
    result.set_item("segmentKeyBase", col_segment_key_base)?;
    result.set_item("text", col_text)?;
    result.set_item("blockIdx", col_block_idx)?;

    Ok(result.into_any().unbind())
}

#[pymodule]
fn dartlab_native_poc(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_text_structure, m)?)?;
    m.add_function(wrap_pyfunction!(parse_text_structure_batch, m)?)?;
    m.add_function(wrap_pyfunction!(parse_text_structure_columnar, m)?)?;
    Ok(())
}
