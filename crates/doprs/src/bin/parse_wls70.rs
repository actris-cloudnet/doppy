use doprs::raw::wls70;

fn main() {
    let path = std::env::args().nth(1).unwrap();
    let file = std::fs::File::open(path).unwrap();
    let a = wls70::from_file_src(&file).unwrap();
    dbg!(a);
}
