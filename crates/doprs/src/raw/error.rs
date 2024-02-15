use std::fmt;

#[derive(Debug, Clone)]
pub struct RawParseError {
    message: String,
}

impl Default for RawParseError {
    fn default() -> Self {
        Self::new()
    }
}

impl RawParseError {
    pub fn new() -> Self {
        Self {
            message: String::new(),
        }
    }
}

impl fmt::Display for RawParseError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "RawParseError: {}", self.message)
    }
}
impl From<std::io::Error> for RawParseError {
    fn from(err: std::io::Error) -> Self {
        RawParseError {
            message: err.to_string(),
        }
    }
}
impl From<Box<dyn std::error::Error>> for RawParseError {
    fn from(err: Box<dyn std::error::Error>) -> Self {
        RawParseError {
            message: err.to_string(),
        }
    }
}
impl From<String> for RawParseError {
    fn from(s: String) -> RawParseError {
        RawParseError { message: s }
    }
}

impl From<std::num::ParseFloatError> for RawParseError {
    fn from(err: std::num::ParseFloatError) -> RawParseError {
        RawParseError {
            message: err.to_string(),
        }
    }
}
impl From<std::str::Utf8Error> for RawParseError {
    fn from(err: std::str::Utf8Error) -> RawParseError {
        RawParseError {
            message: err.to_string(),
        }
    }
}
impl From<chrono::ParseError> for RawParseError {
    fn from(err: chrono::ParseError) -> RawParseError {
        RawParseError {
            message: err.to_string(),
        }
    }
}
impl From<std::num::ParseIntError> for RawParseError {
    fn from(err: std::num::ParseIntError) -> RawParseError {
        RawParseError {
            message: err.to_string(),
        }
    }
}

impl From<regex::Error> for RawParseError {
    fn from(err: regex::Error) -> RawParseError {
        RawParseError {
            message: err.to_string(),
        }
    }
}

impl From<&str> for RawParseError {
    fn from(s: &str) -> RawParseError {
        RawParseError {
            message: s.to_string(),
        }
    }
}
