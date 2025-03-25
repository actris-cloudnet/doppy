use doprs::raw::wls77;

fn main() {
    let path = std::env::args().nth(1).unwrap();
    let file = std::fs::File::open(path).unwrap();
    let _a = wls77::from_file_src(&file).unwrap();
}
