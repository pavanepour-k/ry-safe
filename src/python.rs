use html_escape::{decode_html_entities, encode_text};
use pyo3::prelude::*;
use pyo3::types::{PyString, PyType};

#[pyfunction]
fn escape(py: Python, obj: &PyAny) -> PyResult<Py<Markup>> {
    let text = if obj.is_none() {
        "None"
    } else if let Ok(s) = obj.extract::<&str>() {
        s
    } else if let Ok(_) = obj.getattr("__html__") {
        let html_result = obj.call_method0("__html__")?;
        return Ok(Markup::new(py, html_result.extract::<&str>()?)?);
    } else {
        &obj.str()?.to_str()?
    };

    let mut escaped = encode_text(text).to_string();
    escaped = escaped.replace("&#39;", "&#x27;");
    Markup::new(py, &escaped)
}

#[pyfunction]
fn escape_silent(py: Python, obj: &PyAny) -> PyResult<Py<Markup>> {
    if obj.is_none() {
        Markup::new(py, "")
    } else {
        escape(py, obj)
    }
}

#[pyfunction]
fn soft_str(obj: &PyAny) -> PyResult<&PyAny> {
    Ok(obj)
}

#[pyfunction]
fn unescape(_py: Python, obj: &PyAny) -> PyResult<String> {
    let text = if let Ok(s) = obj.extract::<&str>() {
        s
    } else {
        obj.str()?.to_str()?
    };
    let mut result = decode_html_entities(text).to_string();
    result = result.replace("&#x27;", "'");
    Ok(result)
}

#[pyclass(extends=PyString)]
pub struct Markup;

#[pymethods]
impl Markup {
    #[new]
    pub fn new(py: Python, text: &str) -> PyResult<Py<Self>> {
        let string = PyString::new(py, text);
        Ok((Self {}, string).into_py(py))
    }

    fn __html__(&self) -> PyResult<&PyString> {
        let base: &PyString = self.as_ref();
        Ok(base)
    }

    fn __add__(&self, py: Python, other: &PyAny) -> PyResult<Py<Markup>> {
        let base: &PyString = self.as_ref();
        let base_str = base.to_str()?;

        let combined = if let Ok(markup) = other.extract::<PyRef<Markup>>() {
            let other_str: &PyString = markup.as_ref();
            format!("{}{}", base_str, other_str.to_str()?)
        } else if let Ok(s) = other.extract::<&str>() {
            format!("{}{}", base_str, encode_text(s))
        } else if let Ok(_) = other.getattr("__html__") {
            let html = other.call_method0("__html__")?;
            format!("{}{}", base_str, html.extract::<&str>()?)
        } else {
            format!("{}{}", base_str, encode_text(&other.str()?.to_str()?))
        };

        Markup::new(py, &combined)
    }

    fn __mod__(&self, py: Python, args: &PyAny) -> PyResult<Py<Markup>> {
        let base: &PyString = self.as_ref();
        let template = base.to_str()?;

        let formatted = if let Ok(tuple) = args.downcast::<pyo3::types::PyTuple>() {
            let mut result = template.to_string();
            for arg in tuple.iter() {
                if let Some(pos) = result.find("%s") {
                    let value = if let Ok(markup) = arg.extract::<PyRef<Markup>>() {
                        let s: &PyString = markup.as_ref();
                        s.to_str()?.to_string()
                    } else if let Ok(_) = arg.getattr("__html__") {
                        let html = arg.call_method0("__html__")?;
                        html.extract::<&str>()?.to_string()
                    } else {
                        encode_text(&arg.str()?.to_str()?).to_string()
                    };
                    result = format!("{}{}{}", &result[..pos], value, &result[pos + 2..]);
                }
            }
            result
        } else {
            let value = if let Ok(markup) = args.extract::<PyRef<Markup>>() {
                let s: &PyString = markup.as_ref();
                s.to_str()?.to_string()
            } else if let Ok(_) = args.getattr("__html__") {
                let html = args.call_method0("__html__")?;
                html.extract::<&str>()?.to_string()
            } else {
                encode_text(&args.str()?.to_str()?).to_string()
            };
            template.replacen("%s", &value, 1)
        };

        Markup::new(py, &formatted)
    }

    fn unescape(&self) -> PyResult<String> {
        let base: &PyString = self.as_ref();
        let text = base.to_str()?;
        let mut result = decode_html_entities(text).to_string();
        result = result.replace("&#x27;", "'");
        Ok(result)
    }

    fn striptags(&self) -> PyResult<String> {
        let base: &PyString = self.as_ref();
        let text = base.to_str()?;
        let mut result = String::new();
        let mut in_tag = false;

        for ch in text.chars() {
            match ch {
                '<' => in_tag = true,
                '>' => in_tag = false,
                _ if !in_tag => result.push(ch),
                _ => {}
            }
        }

        Ok(result)
    }

    #[classmethod]
    fn escape(_cls: &PyType, py: Python, obj: &PyAny) -> PyResult<Py<Markup>> {
        crate::python::escape(py, obj)
    }
}

#[pymodule]
fn _rysafe(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Markup>()?;
    m.add_function(wrap_pyfunction!(escape, m)?)?;
    m.add_function(wrap_pyfunction!(escape_silent, m)?)?;
    m.add_function(wrap_pyfunction!(soft_str, m)?)?;
    m.add_function(wrap_pyfunction!(unescape, m)?)?;
    Ok(())
}
