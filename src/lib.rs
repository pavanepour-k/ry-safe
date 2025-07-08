#[cfg(feature = "python")]
pub mod python;

pub use html_escape::{decode_html_entities, encode_text};
