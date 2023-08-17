#!/usr/bin/env bash

temp=$( realpath "$0"  )
script_directory=$( dirname "$temp" )

cd $script_directory/..

python run.py \
    --config-dir=recipes \
    --config-name=spheres_sem \
    --multirun \
    blueprints.particles.Bead.number=100,200,300,400,500,600 \
    initial_runtime_state.seed=range\(15\) \
    synth_chain.feature_generation_steps.5.gravity.2=-100,-10000
