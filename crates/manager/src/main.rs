use clap::{Parser, Subcommand};
pub mod generate_samples;
pub mod group;

#[derive(Parser)]
struct Args {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    GenerateSamples,
}

fn main() {
    let args = Args::parse();
    match args.command {
        Commands::GenerateSamples => generate_samples::sample(),
    }
}
