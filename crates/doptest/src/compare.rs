use serde_json::Value;

use crate::types::Diff;

const RTOL: f64 = 1e-6;

fn is_close(actual: f64, expected: f64) -> bool {
    if expected == 0.0 {
        actual == 0.0
    } else {
        ((actual - expected) / expected).abs() <= RTOL
    }
}

fn is_exact_field(name: &str) -> bool {
    name.ends_with("_len") || name == "n_gates" || name == "file_count" || name == "count"
}

pub fn compare_values(expected: &Value, actual: &Value, path: &str) -> Vec<Diff> {
    let mut diffs = Vec::new();

    match (expected, actual) {
        (Value::Object(exp), Value::Object(act)) => {
            for (key, exp_val) in exp {
                let child_path = format!("{path}.{key}");
                match act.get(key) {
                    Some(act_val) => {
                        diffs.extend(compare_values(exp_val, act_val, &child_path));
                    }
                    None => {
                        diffs.push(Diff {
                            field: child_path,
                            expected: exp_val.clone(),
                            actual: Value::Null,
                        });
                    }
                }
            }
        }

        (Value::Number(exp_n), Value::Number(act_n)) => {
            if let (Some(exp_f), Some(act_f)) = (exp_n.as_f64(), act_n.as_f64()) {
                let field_name = path.rsplit('.').next().unwrap_or(path);
                #[allow(clippy::float_cmp)]
                let mismatch = if is_exact_field(field_name) {
                    exp_f != act_f
                } else {
                    !is_close(act_f, exp_f)
                };
                if mismatch {
                    diffs.push(Diff {
                        field: path.to_string(),
                        expected: expected.clone(),
                        actual: actual.clone(),
                    });
                }
            }
        }

        _ => {
            if expected != actual {
                diffs.push(Diff {
                    field: path.to_string(),
                    expected: expected.clone(),
                    actual: actual.clone(),
                });
            }
        }
    }

    diffs
}
