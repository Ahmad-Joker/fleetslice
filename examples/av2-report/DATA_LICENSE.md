# Argoverse 2 attribution and data terms

This directory contains transformed and aggregated results derived from the **Argoverse 2 Motion
Forecasting Dataset**, collected by Argo AI and released by the Argoverse contributors.

Reference: Benjamin Wilson et al., *Argoverse 2: Next Generation Datasets for Self-Driving Perception
and Forecasting*, 2023. [Paper](https://arxiv.org/abs/2301.00493).

Original dataset and terms: https://www.argoverse.org/av2.html

Dataset license: **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International**:
https://creativecommons.org/licenses/by-nc-sa/4.0/

The numeric/trajectory content in these derived reports is shared under the same CC BY-NC-SA 4.0
license, subject to the original dataset terms. The MIT code license does not relicense AV2 data.

Changes: selected the first 128 validation parquet objects in lexicographic order, selected complete
focal tracks, translated positions to their final observation, generated kinematic reference
forecasts, computed per-scene and sliced statistics, and embedded selected trajectories in HTML.
Raw parquet files and maps are not redistributed. The exact object URLs, bytes and SHA-256 hashes
are recorded in `source_manifest.json`.

This is a small nonrandom validation sample, not a full validation or test benchmark. No affiliation,
approval, or endorsement by Argoverse, Argo AI, Tesla, or any other organization is implied.
