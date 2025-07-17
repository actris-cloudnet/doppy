use doprs::raw::halo_hpl;

fn main() {
    let path = std::env::args().nth(1).unwrap();
    let file = std::fs::File::open(path).unwrap();
    let a = halo_hpl::from_file_src(&file).unwrap();
    dbg!(a.info);
}
