use std::ops::RangeInclusive;

use rand::rngs::StdRng;
use rand::{RngExt, SeedableRng};

// ── Types ────────────────────────────────────────────────────────────

#[derive(Debug)]
pub struct ClusteringResult {
    pub k: usize,
    pub inertia: f64,
    pub assignments: Vec<ClusterAssignment>,
    pub selected: Vec<usize>,
    pub cluster_sizes: Vec<usize>,
    /// Pairwise centroid distances sorted ascending: `(cluster_a, cluster_b, distance)`.
    pub centroid_distances: Vec<(usize, usize, f64)>,
}

#[derive(Debug)]
pub struct ClusterAssignment {
    pub index: usize,
    pub cluster: usize,
    pub distance_to_centroid: f64,
}

// ── Distance ─────────────────────────────────────────────────────────

fn distance_sq(a: &[f64], b: &[f64]) -> f64 {
    a.iter().zip(b).map(|(x, y)| (x - y).powi(2)).sum()
}

// ── Standardization ──────────────────────────────────────────────────

#[allow(clippy::cast_precision_loss)]
fn standardize(data: &[Vec<f64>]) -> Vec<Vec<f64>> {
    let n = data.len();
    let d = data[0].len();
    let mut means = vec![0.0; d];
    let mut vars = vec![0.0; d];

    for row in data {
        for (j, &v) in row.iter().enumerate() {
            means[j] += v;
        }
    }
    for m in &mut means {
        *m /= n as f64;
    }

    for row in data {
        for (j, &v) in row.iter().enumerate() {
            vars[j] += (v - means[j]).powi(2);
        }
    }
    let stds: Vec<f64> = vars
        .iter()
        .map(|&v| {
            let s = (v / n as f64).sqrt();
            if s < 1e-12 { 1.0 } else { s }
        })
        .collect();

    data.iter()
        .map(|row| {
            row.iter()
                .enumerate()
                .map(|(j, &v)| (v - means[j]) / stds[j])
                .collect()
        })
        .collect()
}

// ── K-means++ initialization ─────────────────────────────────────────

fn kmeans_pp_init(data: &[Vec<f64>], k: usize, rng: &mut StdRng) -> Vec<Vec<f64>> {
    let n = data.len();
    let mut centroids: Vec<Vec<f64>> = Vec::with_capacity(k);

    centroids.push(data[rng.random_range(0..n)].clone());

    let mut min_dists = vec![f64::MAX; n];

    for _ in 1..k {
        let last = centroids.last().unwrap();
        for (i, row) in data.iter().enumerate() {
            let d = distance_sq(row, last);
            if d < min_dists[i] {
                min_dists[i] = d;
            }
        }

        // Weighted random selection (D^2)
        let total: f64 = min_dists.iter().sum();
        if total < 1e-12 {
            // All points coincide with existing centroids; pick randomly
            centroids.push(data[rng.random_range(0..n)].clone());
            continue;
        }

        let threshold = rng.random_range(0.0..total);
        let mut cumulative = 0.0;
        let mut chosen = n - 1;
        for (i, &d) in min_dists.iter().enumerate() {
            cumulative += d;
            if cumulative >= threshold {
                chosen = i;
                break;
            }
        }
        centroids.push(data[chosen].clone());
    }

    centroids
}

// ── K-means (Lloyd's algorithm) ──────────────────────────────────────

const MAX_ITER: usize = 100;
const N_RESTARTS: usize = 5;

#[allow(clippy::cast_precision_loss)]
fn kmeans_once(data: &[Vec<f64>], k: usize, rng: &mut StdRng) -> (Vec<usize>, Vec<Vec<f64>>, f64) {
    let n = data.len();
    let d = data[0].len();
    let mut centroids = kmeans_pp_init(data, k, rng);
    let mut assignments = vec![0usize; n];
    let mut sums = vec![vec![0.0; d]; k];
    let mut counts = vec![0usize; k];

    for _ in 0..MAX_ITER {
        let mut changed = false;
        for (i, row) in data.iter().enumerate() {
            let mut best_c = 0;
            let mut best_d = f64::MAX;
            for (c, centroid) in centroids.iter().enumerate() {
                let d = distance_sq(row, centroid);
                if d < best_d {
                    best_d = d;
                    best_c = c;
                }
            }
            if assignments[i] != best_c {
                assignments[i] = best_c;
                changed = true;
            }
        }

        for row in &mut sums {
            row.fill(0.0);
        }
        counts.fill(0);
        for (i, row) in data.iter().enumerate() {
            let c = assignments[i];
            counts[c] += 1;
            for (j, &v) in row.iter().enumerate() {
                sums[c][j] += v;
            }
        }

        for c in 0..k {
            if counts[c] == 0 {
                // Empty cluster: re-seed from farthest point
                let farthest = (0..n)
                    .max_by(|&a, &b| {
                        let da = distance_sq(&data[a], &centroids[assignments[a]]);
                        let db = distance_sq(&data[b], &centroids[assignments[b]]);
                        da.total_cmp(&db)
                    })
                    .unwrap();
                centroids[c].clone_from(&data[farthest]);
            } else {
                for j in 0..d {
                    centroids[c][j] = sums[c][j] / counts[c] as f64;
                }
            }
        }

        if !changed {
            break;
        }
    }

    // Compute inertia (sum of squared distances to assigned centroid)
    let inertia: f64 = data
        .iter()
        .enumerate()
        .map(|(i, row)| distance_sq(row, &centroids[assignments[i]]))
        .sum();

    (assignments, centroids, inertia)
}

fn kmeans(data: &[Vec<f64>], k: usize, rng: &mut StdRng) -> (Vec<usize>, Vec<Vec<f64>>, f64) {
    let mut best_assignments = Vec::new();
    let mut best_centroids = Vec::new();
    let mut best_inertia = f64::MAX;

    for _ in 0..N_RESTARTS {
        let (assignments, centroids, inertia) = kmeans_once(data, k, rng);
        if inertia < best_inertia {
            best_inertia = inertia;
            best_assignments = assignments;
            best_centroids = centroids;
        }
    }

    (best_assignments, best_centroids, best_inertia)
}

// ── Elbow detection (Kneedle algorithm) ──────────────────────────────

/// Find the "elbow" in a decreasing curve of (k, inertia) pairs.
/// Returns the index of the elbow point.
#[allow(clippy::cast_precision_loss)]
fn find_elbow(points: &[(usize, f64)]) -> usize {
    if points.len() <= 2 {
        return 0;
    }

    let k_min = points.first().unwrap().0 as f64;
    let k_max = points.last().unwrap().0 as f64;
    let k_range = k_max - k_min;

    let inertia_min = points.iter().map(|p| p.1).reduce(f64::min).unwrap();
    let inertia_max = points.iter().map(|p| p.1).reduce(f64::max).unwrap();
    let inertia_range = inertia_max - inertia_min;

    if k_range < 1e-12 || inertia_range < 1e-12 {
        return 0;
    }

    let x0 = 0.0_f64;
    let y0 = (points[0].1 - inertia_min) / inertia_range;
    let x1 = 1.0_f64;
    let y1 = (points.last().unwrap().1 - inertia_min) / inertia_range;
    let dx = x1 - x0;
    let dy = y1 - y0;
    let line_len = dx.hypot(dy);

    let mut best_idx = 0;
    let mut best_dist = f64::NEG_INFINITY;

    for (i, &(k, inertia)) in points.iter().enumerate() {
        let nx = (k as f64 - k_min) / k_range;
        let ny = (inertia - inertia_min) / inertia_range;
        let dist = (ny - y0).mul_add(dx, -(nx - x0) * dy).abs() / line_len;
        if dist > best_dist {
            best_dist = dist;
            best_idx = i;
        }
    }

    best_idx
}

struct KmeansRun {
    k: usize,
    assignments: Vec<usize>,
    centroids: Vec<Vec<f64>>,
    inertia: f64,
}

// ── Public entry point ───────────────────────────────────────────────

#[allow(clippy::cast_precision_loss)]
pub fn cluster_and_select(
    features: &[Vec<f64>],
    k_range: RangeInclusive<usize>,
    per_cluster: usize,
) -> Result<ClusteringResult, String> {
    let n = features.len();

    let expected_dim = features[0].len();
    for (i, row) in features.iter().enumerate() {
        if row.len() != expected_dim {
            return Err(format!(
                "sample {i}: expected {expected_dim} features, got {}",
                row.len()
            ));
        }
    }

    let features: Vec<Vec<f64>> = features
        .iter()
        .map(|row| {
            row.iter()
                .map(|&v| if v.is_finite() { v } else { 0.0 })
                .collect()
        })
        .collect();

    if n < 2 {
        return Err(format!("need at least 2 samples for clustering, got {n}"));
    }

    let min_k = (*k_range.start()).max(2).min(n - 1);
    let max_k = (*k_range.end()).min(n - 1).max(min_k);

    let data = standardize(&features);

    let mut rng = StdRng::seed_from_u64(42);
    let mut runs: Vec<KmeansRun> = Vec::new();

    for k in min_k..=max_k {
        let (assignments, centroids, inertia) = kmeans(&data, k, &mut rng);
        eprintln!("  k={k:>2}  inertia={inertia:.1}");
        runs.push(KmeansRun {
            k,
            assignments,
            centroids,
            inertia,
        });
    }

    let inertia_points: Vec<(usize, f64)> = runs.iter().map(|r| (r.k, r.inertia)).collect();
    let elbow_idx = find_elbow(&inertia_points);
    let best = runs.swap_remove(elbow_idx);

    let assignments: Vec<ClusterAssignment> = (0..n)
        .map(|i| {
            let c = best.assignments[i];
            ClusterAssignment {
                index: i,
                cluster: c,
                distance_to_centroid: distance_sq(&data[i], &best.centroids[c]).sqrt(),
            }
        })
        .collect();

    let mut selected: Vec<usize> = Vec::new();
    for c in 0..best.k {
        let mut cluster_indices: Vec<usize> = assignments
            .iter()
            .enumerate()
            .filter(|(_, a)| a.cluster == c)
            .map(|(idx, _)| idx)
            .collect();
        cluster_indices.sort_by(|&a, &b| {
            assignments[a]
                .distance_to_centroid
                .total_cmp(&assignments[b].distance_to_centroid)
        });
        selected.extend(cluster_indices.into_iter().take(per_cluster));
    }

    let mut cluster_sizes = vec![0usize; best.k];
    for a in &assignments {
        cluster_sizes[a.cluster] += 1;
    }

    let mut centroid_distances: Vec<(usize, usize, f64)> = Vec::new();
    for i in 0..best.k {
        for j in (i + 1)..best.k {
            let d = distance_sq(&best.centroids[i], &best.centroids[j]).sqrt();
            centroid_distances.push((i, j, d));
        }
    }
    centroid_distances.sort_by(|a, b| a.2.total_cmp(&b.2));

    Ok(ClusteringResult {
        k: best.k,
        inertia: best.inertia,
        assignments,
        selected,
        cluster_sizes,
        centroid_distances,
    })
}
