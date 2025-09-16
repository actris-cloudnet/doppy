use chrono::NaiveDate;
use clap::{Args, Parser, Subcommand};
use download::download;
use raw_files::{get_metadata, get_metadata_for_day};
use testfile::add_testcase_from_instrument_uploads;
use uuid::Uuid;

pub mod download;
pub mod raw_files;
pub mod testfile;

#[derive(Debug, Parser)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Debug, Args)]
struct TestArgs {
    r#type: testfile::TestType,
    #[arg(short, long)]
    description: Option<String>,
    #[arg(long)]
    dry_run: bool,
}

#[derive(Debug, Subcommand)]
enum Commands {
    AddFile {
        #[command(flatten)]
        testargs: TestArgs,
        filename: String,
        file_uuid: Uuid,
    },
    AddDay {
        #[command(flatten)]
        testargs: TestArgs,
        site_id: String,
        measurement_date: NaiveDate,
        instrument_uuid: Uuid,
        #[arg(short, long)]
        include_filename_re: Option<String>,
        #[arg(short, long)]
        exclude_filename_re: Option<String>,
    },
    Download,
}

fn main() {
    let args = Cli::parse();
    match args.command {
        Commands::AddFile {
            ref testargs,
            ref filename,
            ref file_uuid,
        } => {
            add_file(testargs, filename, file_uuid);
        }
        Commands::AddDay {
            ref testargs,
            ref site_id,
            ref measurement_date,
            ref instrument_uuid,
            ref include_filename_re,
            ref exclude_filename_re,
        } => {
            add_day(
                testargs,
                site_id,
                measurement_date,
                instrument_uuid,
                include_filename_re.as_deref(),
                exclude_filename_re.as_deref(),
            );
        }
        Commands::Download => download(),
    }
}

fn add_file(testargs: &TestArgs, filename: &str, uuid: &Uuid) {
    let iu = get_metadata(filename, uuid);
    if testargs.dry_run {
        println!("Dry run: {iu:#?}");
        return;
    }
    add_testcase_from_instrument_uploads(&testargs.r#type, testargs.description.as_deref(), &[iu]);
}

fn add_day(
    testargs: &TestArgs,
    site_id: &str,
    measurement_date: &NaiveDate,
    instrument_uuid: &Uuid,
    include_filename_re: Option<&str>,
    exclude_filename_re: Option<&str>,
) {
    let uploads = get_metadata_for_day(
        site_id,
        measurement_date,
        instrument_uuid,
        include_filename_re,
        exclude_filename_re,
    );
    if testargs.dry_run {
        let mut fnames: Vec<_> = uploads.iter().map(|u| u.filename.clone()).collect();
        fnames.sort();
        for fname in fnames {
            println!("Dry run: {fname}");
        }
        return;
    }
    add_testcase_from_instrument_uploads(
        &testargs.r#type,
        testargs.description.as_deref(),
        &uploads,
    );
}
