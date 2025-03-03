use clap::{Parser, Subcommand};
pub mod generate_filetype_docs;
pub mod generate_raw_tests;
pub mod group;

#[derive(Parser)]
struct Args {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    GenerateFileTypeDocs,
    GenerateRawTests,
}

fn main() {
    let args = Args::parse();
    match args.command {
        Commands::GenerateFileTypeDocs => generate_filetype_docs::generate_filetype_docs(),
        Commands::GenerateRawTests => generate_raw_tests::generate_raw_tests(),
    }
}
