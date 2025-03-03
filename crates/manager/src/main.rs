use clap::{Parser, Subcommand};
pub mod generate_filetype_docs;
pub mod group;
pub mod raw_tests;

#[derive(Parser)]
struct Args {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    GenerateFileTypeDocs,
    GenerateRawTests,
    DownloadRawTests,
}

fn main() {
    let args = Args::parse();
    match args.command {
        Commands::GenerateFileTypeDocs => generate_filetype_docs::generate_filetype_docs(),
        Commands::GenerateRawTests => raw_tests::generate_raw_tests(),
        Commands::DownloadRawTests => {
            let rt = tokio::runtime::Runtime::new().unwrap();
            rt.block_on(raw_tests::download_raw_tests());
        }
    }
}
